from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect

from django.core.paginator import Paginator
import os
import json
import time
from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout

from django.contrib import messages

from django.db import transaction
from django.db.models import Sum, Avg, Count, Q, F
from django.db.models.functions import Coalesce
from django.utils import timezone

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from datetime import date
import datetime
import qrcode
import json

from app_facture.utils import render_to_pdf

from app_facture.models import Detail_facture
from app_facture.models.appartement import Appartement
from app_facture.models.facture import Facture
from app_facture.models.produit import Produit
from app_facture.models.user import Profile, User
from app_facture.models.lot import Lot
from app_facture.models.mouvement_stock import MouvementStock


# ==========================================================
# CONSTANTES TVA
# ==========================================================

TVA_TAUX = Decimal("16.00")
TVA_DIVISEUR = Decimal("1.16")


def calcul_tva_depuis_ttc(prix_ttc):
    """
    Calcule le prix HT et la TVA à partir d'un prix TTC.

    Exemple :
        TTC = 11 600
        HT  = 10 000
        TVA = 1 600
    """

    prix_ttc = Decimal(prix_ttc or "0.00")

    prix_ht = (
        prix_ttc / TVA_DIVISEUR
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    tva = (
        prix_ttc - prix_ht
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    return prix_ht, tva


# ==========================================================
# HOME
# ==========================================================

@login_required(login_url="sign_in")
def home(request):

    mois = datetime.date.today().month
    annee = datetime.date.today().year
    aujourd_hui = datetime.date.today()

    # ======================================================
    # NOMBRE DE PRODUITS
    # ======================================================

    nbrp = Produit.objects.count()

    # ======================================================
    # FACTURES VALIDÉES
    # ======================================================

    factj = Facture.objects.filter(
        createdAt__date=aujourd_hui,
        imprimer=True
    )

    factm = Facture.objects.filter(
        createdAt__date__month=mois,
        createdAt__date__year=annee,
        imprimer=True
    )

    factan = Facture.objects.filter(
        createdAt__date__year=annee,
        imprimer=True
    )

    # ======================================================
    # NOMBRE DE FACTURES
    # ======================================================

    totalFacture = factj.count()
    totalFactureM = factm.count()
    totalFactureA = factan.count()

    # ======================================================
    # CA TTC
    # ======================================================

    somme = factj.aggregate(
        total=Coalesce(
            Sum("total_ttc"),
            Decimal("0.00")
        )
    )["total"]

    sommeMois = factm.aggregate(
        total=Coalesce(
            Sum("total_ttc"),
            Decimal("0.00")
        )
    )["total"]

    sommeAn = factan.aggregate(
        total=Coalesce(
            Sum("total_ttc"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # CA HT
    # ======================================================

    somme_ht = factj.aggregate(
        total=Coalesce(
            Sum("total_ht"),
            Decimal("0.00")
        )
    )["total"]

    sommeMois_ht = factm.aggregate(
        total=Coalesce(
            Sum("total_ht"),
            Decimal("0.00")
        )
    )["total"]

    sommeAn_ht = factan.aggregate(
        total=Coalesce(
            Sum("total_ht"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # TVA COLLECTÉE
    # ======================================================

    tva_jour = factj.aggregate(
        total=Coalesce(
            Sum("total_tva"),
            Decimal("0.00")
        )
    )["total"]

    tva_mois = factm.aggregate(
        total=Coalesce(
            Sum("total_tva"),
            Decimal("0.00")
        )
    )["total"]

    tva_annee = factan.aggregate(
        total=Coalesce(
            Sum("total_tva"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # PRODUITS LES PLUS VENDUS
    # ======================================================
    #
    # On utilise Detail_facture et non Produit.quantite.
    #
    # Produit.quantite = stock actuel
    # Detail_facture.quantite = quantité réellement vendue
    #
    # On ne prend que les factures validées.
    # ======================================================

    details_ventes = Detail_facture.objects.filter(
        facture__imprimer=True,
        facture__createdAt__date__year=annee
    )

    produits_populaires = (
        details_ventes
        .values(
            "produit__id",
            "produit__nom"
        )
        .annotate(
            quantite_vendue=Coalesce(
                Sum("quantite"),
                Decimal("0.00")
            ),
            chiffre_affaires=Coalesce(
                Sum(
                    F("quantite") * F("pu_ttc")
                ),
                Decimal("0.00")
            )
        )
        .order_by("-quantite_vendue")[:10]
    )

    # ======================================================
    # PRODUITS LES PLUS VENDUS AUJOURD'HUI
    # ======================================================

    produits_populaires_jour = (
        Detail_facture.objects.filter(
            facture__imprimer=True,
            facture__createdAt__date=aujourd_hui
        )
        .values(
            "produit__id",
            "produit__nom"
        )
        .annotate(
            quantite_vendue=Coalesce(
                Sum("quantite"),
                Decimal("0.00")
            ),
            chiffre_affaires=Coalesce(
                Sum(
                    F("quantite") * F("pu_ttc")
                ),
                Decimal("0.00")
            )
        )
        .order_by("-quantite_vendue")[:10]
    )

    # ======================================================
    # CONTEXT
    # ======================================================

    ctx = {
        "hm": "active",

        # Factures
        "totalFacture": totalFacture,
        "totalFactureM": totalFactureM,
        "totalFactureA": totalFactureA,

        # CA TTC
        "somme": somme,
        "sommeMois": sommeMois,
        "sommeAn": sommeAn,

        # CA HT
        "somme_ht": somme_ht,
        "sommeMois_ht": sommeMois_ht,
        "sommeAn_ht": sommeAn_ht,

        # TVA
        "tva_jour": tva_jour,
        "tva_mois": tva_mois,
        "tva_annee": tva_annee,

        # Produits
        "nbrp": nbrp,
        "produits_populaires": produits_populaires,
        "produits_populaires_jour": produits_populaires_jour,
    }

    return render(
        request,
        "pages/home.html",
        ctx
    )
# ==========================================================
# APPARTEMENTS
# ==========================================================

@login_required(login_url="sign_in")
def appartement(request):

    recherche = request.GET.get(
        "q",
        request.POST.get("rech", "")
    ).strip()

    queryset = Appartement.objects.all().order_by("-id")

    if recherche:

        queryset = queryset.filter(
            nom__icontains=recherche
        )

    paginator = Paginator(
        queryset,
        4
    )

    page_number = request.GET.get("page")

    pages = paginator.get_page(
        page_number
    )

    compte = paginator.count

    ctx = {
        "compte": compte,
        "appartement": pages,
        "lapr": "active",
        "noms": request.user.noms,
        "profile": request.user.profile,
        "pages": pages,
        "page_obj": pages,
        "recherche": recherche,
    }

    return render(
        request,
        "pages/appartement.html",
        ctx
    )


@login_required(login_url="sign_in")
def fAppartement(request):

    nbrhomme = 0
    nbrFemme = 0

    ctx = {
        "lfact": "active",
        "nbrhomme": nbrhomme,
        "noms": request.user.noms,
        "profile": request.user.profile,
        "nbrFemme": nbrFemme,
    }

    return render(
        request,
        "formulaires/appartement.html",
        ctx
    )


@login_required(login_url="sign_in")
def addAppartement(request):

    msg = None
    msok = None

    paginator = Paginator(
        Appartement.objects.all().order_by("-id"),
        4
    )

    page = request.GET.get("page")

    pages = paginator.get_page(page)

    compte = paginator.count

    if request.method == "POST":

        noms = request.POST.get(
            "nom",
            ""
        ).strip()

        ver_nom = Appartement.objects.filter(
            nom=noms.upper()
        )

        if noms == "":
            msg = "Veuillez remplir le nom"

        elif ver_nom.exists():
            msg = "Un appartement portant ce nom existe déjà"

        else:

            ap = Appartement(
                nom=noms.upper()
            )

            ap.save()

            msok = "Opération réussie"

            return HttpResponseRedirect(
                "/appartement/"
            )

    ctx = {
        "msg": msg,
        "msok": msok,
        "compte": compte,
        "appartement": pages,
        "noms": request.user.noms,
        "profile": request.user.profile,
        "lapr": "active",
        "pages": pages,
    }

    return render(
        request,
        "formulaires/appartement.html",
        ctx
    )


@login_required(login_url="sign_in")
def modAppartement(request, id):

    ap = Appartement.objects.get(
        pk=id
    )

    ctx = {
        "ap": ap
    }

    return render(
        request,
        "formulaires/modAppartement.html",
        ctx
    )


@login_required(login_url="sign_in")
def updateAppartement(request, id):

    appar = Appartement.objects.get(
        pk=id
    )

    msg = None
    msok = None

    if request.method == "POST":

        nom = request.POST.get(
            "nom",
            ""
        ).strip()

        if nom == "":

            msg = "Veuillez remplir le nom"

        else:

            appar.nom = nom.upper()

            appar.save()

            msok = nom + " modifié avec succès"

            return HttpResponseRedirect(
                "/appartement/"
            )

    ctx = {
        "msg": msg,
        "msok": msok,
        "noms": request.user.noms,
        "profile": request.user.profile,
        "ap": appar,
    }

    return render(
        request,
        "formulaires/modAppartement.html",
        ctx
    )


@login_required(login_url="sign_in")
def deleteAppartement(request, id):

    p = Appartement.objects.get(
        pk=id
    )

    prod = Produit.objects.filter(
        appartement__id=p.id
    )

    if prod.exists():

        return HttpResponseRedirect(
            "/appartement/"
        )

    p.delete()

    return HttpResponseRedirect(
        "/appartement/"
    )


# ==========================================================
# PRODUITS
# ==========================================================

@login_required(login_url="sign_in")
def produit(request):

    recherche = request.GET.get(
        "q",
        request.POST.get("rech", "")
    ).strip()

    queryset = Produit.objects.select_related(
        "appartement"
    ).all().order_by("-id")

    if recherche:

        queryset = queryset.filter(
            nom__icontains=recherche
        )

    paginator = Paginator(
        queryset,
        20
    )

    page_number = request.GET.get(
        "page"
    )

    pages = paginator.get_page(
        page_number
    )

    compte = paginator.count

    tot_produit = Produit.objects.count()

    ctx = {
        "compte": compte,
        "produit": pages,
        "lproduit": "active",
        "tot_produit": tot_produit,
        "noms": request.user.noms,
        "profile": request.user.profile,
        "pages": pages,
        "page_obj": pages,
        "recherche": recherche,
    }

    return render(
        request,
        "pages/produit.html",
        ctx
    )


@login_required(login_url="sign_in")
def fProduit(request):

    appart = Appartement.objects.all()

    ctx = {
        "appart": appart,
        "noms": request.user.noms,
        "profile": request.user.profile,
    }

    return render(
        request,
        "formulaires/produit.html",
        ctx
    )


@login_required(login_url="sign_in")
def addProduit(request):

    appart = Appartement.objects.all()

    compte = Produit.objects.count()

    msg = None
    msok = None

    if request.method == "POST":

        nom = request.POST.get(
            "nom",
            ""
        ).strip()

        pu = request.POST.get(
            "pu",
            "0"
        ).strip()

        appartement = request.POST.get(
            "appartement",
            ""
        )

        ver_nom_prod = Produit.objects.filter(
            nom=nom.upper()
        )

        if nom == "":

            msg = "Veuillez remplir le nom"

        elif pu == "":

            msg = "Veuillez remplir le pu"

        elif ver_nom_prod.exists():

            msg = "Un produit porte déjà ce nom"

        else:

            try:

                prix = Decimal(pu)

                if prix < 0:
                    raise ValueError

            except (
                ValueError,
                TypeError,
                InvalidOperation
            ):

                msg = "Prix doit être un numérique"

            else:

                if appartement == "":

                    msg = "Veuillez remplir le appartement"

                else:

                    apr = Appartement.objects.get(
                        pk=appartement
                    )

                    pr = Produit(
                        nom=nom.upper(),
                        pu=prix,
                        appartement=apr
                    )

                    pr.save()

                    msok = "Opération réussie"

                    return HttpResponseRedirect(
                        "/produit/"
                    )

    ctx = {
        "msg": msg,
        "msok": msok,
        "compte": compte,
        "noms": request.user.noms,
        "profile": request.user.profile,
        "appart": appart,
    }

    return render(
        request,
        "formulaires/produit.html",
        ctx
    )


@login_required(login_url="sign_in")
def modProduit(request, id):

    pr = Produit.objects.get(
        id=id
    )

    appart = Appartement.objects.all()

    ctx = {
        "pr": pr,
        "appart": appart,
        "noms": request.user.noms,
        "profile": request.user.profile,
    }

    return render(
        request,
        "formulaires/modProduit.html",
        ctx
    )


@login_required(login_url="sign_in")
def updateProduit(request, id):

    appart = Appartement.objects.all()

    pr = Produit.objects.get(
        pk=id
    )

    msg = None
    msok = None

    if request.method == "POST":

        nom = request.POST.get(
            "nom",
            ""
        ).strip()

        pu = request.POST.get(
            "pu",
            "0"
        ).strip()

        appartement = request.POST.get(
            "appartement",
            ""
        )

        if nom == "":

            msg = "Veuillez remplir le nom"

        elif pu == "":

            msg = "Veuillez remplir le pu"

        elif appartement == "":

            msg = "Veuillez remplir le appartement"

        else:

            try:

                prix = Decimal(pu)

                if prix < 0:
                    raise ValueError

            except (
                ValueError,
                TypeError,
                InvalidOperation
            ):

                msg = "Prix doit être un numérique"

            else:

                apr = Appartement.objects.get(
                    pk=appartement
                )

                pr.nom = nom.upper()
                pr.appartement = apr

                # IMPORTANT :
                # le prix du produit reste stocké en TTC
                pr.pu = prix

                pr.save()

                msok = nom + " modifié avec succès"

                return HttpResponseRedirect(
                    "/produit/"
                )

    ctx = {
        "msg": msg,
        "msok": msok,
        "appart": appart,
        "noms": request.user.noms,
        "profile": request.user.profile,
        "pr": pr,
    }

    return render(
        request,
        "formulaires/modProduit.html",
        ctx
    )


@login_required(login_url="sign_in")
def deleteProduit(request, id):

    p = Produit.objects.get(
        pk=id
    )

    dt = Detail_facture.objects.filter(
        produit__id=p.id
    )

    if dt.exists():

        return HttpResponseRedirect(
            "/produit/"
        )

    p.delete()

    return HttpResponseRedirect(
        "/produit/"
    )


# ==========================================================
# UTILISATEURS
# ==========================================================

@login_required(login_url="sign_in")
def users(request):

    recherche = request.GET.get(
        "q",
        request.POST.get("rech", "")
    ).strip()

    queryset = User.objects.all().order_by(
        "-id"
    )

    if recherche:

        queryset = queryset.filter(
            Q(username__icontains=recherche)
            | Q(noms__icontains=recherche)
            | Q(email__icontains=recherche)
        )

    paginator = Paginator(
        queryset,
        20
    )

    page_number = request.GET.get(
        "page"
    )

    pages = paginator.get_page(
        page_number
    )

    compte = paginator.count

    ctx = {
        "compte": compte,
        "users": pages,
        "luser": "active",
        "noms": request.user.noms,
        "profile": request.user.profile,
        "pages": pages,
        "page_obj": pages,
        "recherche": recherche,
    }

    return render(
        request,
        "user/user.html",
        ctx
    )


@login_required(login_url="sign_in")
def fUser(request):

    profiles = Profile.objects.all()

    ctx = {
        "pro": profiles
    }

    return render(
        request,
        "formulaires/FUser.html",
        ctx
    )

@login_required(login_url="sign_in")
def addUser(request):

    profiles = Profile.objects.all()

    msg = None
    msok = None

    if request.method == "POST":

        profile = request.POST.get(
            "profile",
            ""
        ).strip()

        noms = request.POST.get(
            "noms",
            ""
        ).strip()

        username = request.POST.get(
            "username",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        # ==================================================
        # VALIDATIONS
        # ==================================================

        if email == "":
            msg = "Veuillez remplir le mail"

        elif profile == "":
            msg = "Veuillez choisir le profil"

        elif noms == "":
            msg = "Veuillez remplir les noms"

        elif username == "":
            msg = "Veuillez remplir le nom utilisateur"

        elif password == "":
            msg = "Veuillez remplir le mot de passe"

        elif User.objects.filter(
            username=username
        ).exists():
            msg = "Ce nom utilisateur existe déjà"

        elif User.objects.filter(
            email=email
        ).exists():
            msg = "Cette adresse mail existe déjà"

        else:

            # ==================================================
            # PROFIL
            # ==================================================

            pro = get_object_or_404(
                Profile,
                pk=profile
            )

            # ==================================================
            # CRÉATION UTILISATEUR
            # ==================================================

            u = User(
                noms=noms.upper(),
                profile=pro,
                username=username.upper(),
                email=email,
                is_active=True
            )

            # ==================================================
            # MOT DE PASSE HASHÉ
            # ==================================================

            u.set_password(
                password
            )

            u.save()

            msok = (
                username
                + " est enregistré comme utilisateur"
            )

            return redirect(
                "users"
            )

    return render(
        request,
        "formulaires/FUser.html",
        {
            "msg": msg,
            "msok": msok,
            "pro": profiles
        }
    )

@login_required(login_url="sign_in")
def modifierUser(request, id):

    user = User.objects.get(
        pk=id
    )

    profile = Profile.objects.all()

    ctx = {
        "user": user,
        "pro": profile
    }

    return render(
        request,
        "formulaires/FUserMod.html",
        ctx
    )


@login_required(login_url="sign_in")
def updateUser(request, id):

    user = User.objects.get(
        pk=id
    )

    profiles = Profile.objects.all()

    msg = None
    msok = None

    if request.method == "POST":

        profile = request.POST.get(
            "profile",
            ""
        )

        noms = request.POST.get(
            "noms",
            ""
        )

        username = request.POST.get(
            "username",
            ""
        )

        email = request.POST.get(
            "email",
            ""
        )

        if email == "":

            msg = "Veuillez remplir le mail"

        elif profile == "":

            msg = "Veuillez choisir le profile"

        elif noms == "":

            msg = "Veuillez remplir les noms"

        elif username == "":

            msg = "Veuillez remplir le nom utilisateur"

        else:

            pro = Profile.objects.get(
                pk=profile
            )

            user.noms = noms.upper()
            user.profile = pro
            user.username = username.upper()
            user.email = email
            user.is_active = True

            user.save()

            msok = username + " a été modifié"

            return HttpResponseRedirect(
                "/users/"
            )

    return render(
        request,
        "formulaires/FUser.html",
        {
            "msg": msg,
            "msok": msok,
            "pro": profiles,
            "user": user,
        }
    )


@login_required(login_url="sign_in")
def deleteUser(request, id):

    user = User.objects.get(
        pk=id
    )

    user.delete()

    return HttpResponseRedirect(
        "/users/"
    )


# ==========================================================
# AUTHENTIFICATION
# ==========================================================

def login(request):

    return render(
        request,
        "user/login.html"
    )


def sign_in(request):

    msg = None

    if request.method == "POST":

        username = request.POST.get(
            "username",
            None
        )

        password = request.POST.get(
            "password",
            None
        )

        user = User.objects.filter(
            username=username
        ).first()

        if user:

            auth_user = authenticate(
                username=user.username,
                password=password
            )

            if auth_user:

                auth_login(
                    request,
                    auth_user
                )

                return redirect(
                    "home"
                )

            else:

                msg = "Mot de passe incorrect"

        else:

            msg = "Utilisateur inexistant"

    ctx = {
        "msg": msg
    }

    return render(
        request,
        "user/login.html",
        ctx
    )


def log_out(request):

    logout(request)

    return redirect(
        "sign_in"
    )



# ==========================================================
# FACTURES
# ==========================================================

@login_required(login_url="sign_in")
def facture(request):

    datej = datetime.date.today()

    recherche = request.GET.get(
        "q",
        request.POST.get("rech", "")
    ).strip()

    # ======================================================
    # PROFIL UTILISATEUR
    # ======================================================

    profile = getattr(
        request.user,
        "profile",
        None
    )

    # ======================================================
    # FACTURES
    # ======================================================

    if profile and profile.id == 3:

        factj = Facture.objects.filter(
            createdAt__date=datej,
            user=request.user,
            imprimer=True
        )

        queryset = Facture.objects.filter(
            user=request.user
        )

    else:

        factj = Facture.objects.filter(
            createdAt__date=datej,
            imprimer=True
        )

        queryset = Facture.objects.all()

    # ======================================================
    # NOMBRE DE FACTURES VALIDÉES DU JOUR
    # ======================================================

    nbr = factj.count()

    # ======================================================
    # CA TTC DU JOUR
    # ======================================================

    somme = factj.aggregate(
        total=Coalesce(
            Sum("total_ttc"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # CA HT DU JOUR
    # ======================================================

    somme_ht = factj.aggregate(
        total=Coalesce(
            Sum("total_ht"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # TVA DU JOUR
    # ======================================================

    somme_tva = factj.aggregate(
        total=Coalesce(
            Sum("total_tva"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # RECHERCHE
    # ======================================================

    if recherche:

        queryset = queryset.filter(
            id__icontains=recherche
        )

    # ======================================================
    # TRI
    # ======================================================

    queryset = queryset.order_by(
        "-id"
    )

    # ======================================================
    # PAGINATION
    # ======================================================

    paginator = Paginator(
        queryset,
        16
    )

    page_number = request.GET.get(
        "page"
    )

    pages = paginator.get_page(
        page_number
    )

    compte = paginator.count

    # ======================================================
    # CONTEXT
    # ======================================================

    ctx = {

        "compte": compte,

        "facture": pages,

        "lfact": "active",

        # ==========================
        # TTC
        # ==========================

        "somme": somme,

        # ==========================
        # HT
        # ==========================

        "somme_ht": somme_ht,

        # ==========================
        # TVA
        # ==========================

        "somme_tva": somme_tva,

        # ==========================
        # NOMBRE FACTURES
        # ==========================

        "facture_total_jour": nbr,

        # ==========================
        # UTILISATEUR
        # ==========================

        "noms": request.user.noms,

        "profile": profile,

        # ==========================
        # PAGINATION
        # ==========================

        "pages": pages,

        "page_obj": pages,

        # ==========================
        # RECHERCHE
        # ==========================

        "recherche": recherche,
    }

    return render(
        request,
        "pages/facture.html",
        ctx
    )

@login_required(login_url="sign_in")
def addFacture(request):

    f = Facture.objects.create(
        user=request.user
    )

    return HttpResponseRedirect(
        "/facture/"
    )


# ==========================================================
# DETAILS FACTURE
# ==========================================================

@login_required(login_url="sign_in")
def detaiFacture(request, id):

    # ======================================================
    # FACTURE
    # ======================================================

    sel_facture = get_object_or_404(
        Facture,
        id=id
    )

    # ======================================================
    # PRODUITS
    # ======================================================

    liste_produit = Produit.objects.all()

    data_produit = []

    # ======================================================
    # PRODUITS NON PRÉSENTS DANS LA FACTURE
    # ======================================================

    for lp in liste_produit:

        existe = Detail_facture.objects.filter(
            facture_id=sel_facture.id,
            produit_id=lp.id
        ).exists()

        if not existe:

            data_produit.append({
                "id": lp.id,
                "nom": lp.nom
            })

    # ======================================================
    # RECHERCHE
    # ======================================================

    recherche = request.GET.get(
        "q",
        request.POST.get("rech", "")
    ).strip()

    # ======================================================
    # DÉTAILS DE LA FACTURE
    # ======================================================

    queryset = Detail_facture.objects.filter(
        facture_id=sel_facture.id
    ).select_related(
        "produit"
    )

    if recherche:

        queryset = queryset.filter(
            produit__nom__icontains=recherche
        )

    queryset = queryset.order_by(
        "-id"
    )

    # ======================================================
    # PAGINATION
    # ======================================================

    paginator = Paginator(
        queryset,
        20
    )

    page_number = request.GET.get(
        "page"
    )

    list_facture = paginator.get_page(
        page_number
    )

    compte = paginator.count

    # ======================================================
    # PRÉPARATION DES LIGNES
    # ======================================================

    data_liste = []

    for t in list_facture:

        # --------------------------------------------------
        # Prix TTC
        # --------------------------------------------------

        pu_ttc = (
            t.pu_ttc
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # Prix HT
        # --------------------------------------------------

        pu_ht = (
            t.pu_ht
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # TVA unitaire
        # --------------------------------------------------

        tva_unitaire = (
            t.tva_unitaire
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # Quantité
        # --------------------------------------------------

        quantite = (
            t.quantite
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # Total TTC de la ligne
        # --------------------------------------------------

        total_ligne_ttc = (
            pu_ttc * quantite
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # --------------------------------------------------
        # Total HT de la ligne
        # --------------------------------------------------

        total_ligne_ht = (
            pu_ht * quantite
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # --------------------------------------------------
        # Total TVA de la ligne
        # --------------------------------------------------

        total_ligne_tva = (
            tva_unitaire * quantite
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # --------------------------------------------------
        # Données envoyées au template
        # --------------------------------------------------

        data_liste.append({

            "id": t.id,

            "produit": t.produit,

            # Prix unitaires
            "pu": pu_ttc,
            "pu_ttc": pu_ttc,
            "pu_ht": pu_ht,
            "tva_unitaire": tva_unitaire,

            # Taux TVA
            "taux_tva": t.taux_tva,

            # Quantité
            "qte": quantite,
            "quantite": quantite,

            # Totaux ligne
            "total": total_ligne_ttc,
            "total_ttc": total_ligne_ttc,
            "total_ht": total_ligne_ht,
            "total_tva": total_ligne_tva,
        })

    # ======================================================
    # TOTAUX DE LA FACTURE
    # ======================================================
    #
    # On récupère les totaux enregistrés dans Facture.
    #
    # Cela permet d'avoir le total de TOUTE la facture,
    # même lorsque la facture contient plusieurs pages.
    # ======================================================

    total_ht = (
        sel_facture.total_ht
        or Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    total_tva = (
        sel_facture.total_tva
        or Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    total_ttc = (
        sel_facture.total_ttc
        or Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    # ======================================================
    # CONTEXT
    # ======================================================

    ctx = {

        # Facture
        "sel_facture": sel_facture,

        # Détails
        "list_facture": data_liste,

        # Menu actif
        "Llist_facture": "active",

        # Produits disponibles
        "liste_produit": data_produit,

        # --------------------------------------------------
        # TOTAUX
        # --------------------------------------------------

        # Variables utilisées directement dans le template
        "total_ht": total_ht,
        "total_tva": total_tva,
        "sommefac": total_ttc,

        # Alias supplémentaires
        "somme_ht": total_ht,
        "somme_tva": total_tva,
        "somme_ttc": total_ttc,

        # --------------------------------------------------
        # AUTRES INFORMATIONS
        # --------------------------------------------------

        "compte": compte,

        # Pagination
        "pages": list_facture,
        "page_obj": list_facture,

        # Recherche
        "recherche": recherche,
    }

    # ======================================================
    # RENDU DU TEMPLATE
    # ======================================================

    return render(
        request,
        "pages/detailFacture.html",
        ctx
    )

@login_required(login_url="sign_in")
def deletedetailFacture(request, id):

    df = get_object_or_404(
        Detail_facture,
        pk=id
    )

    dt = get_object_or_404(
        Facture,
        pk=df.facture.id
    )

    id_facture = dt.id

    if dt.imprimer:

        messages.warning(
            request,
            "Impossible de modifier une facture déjà validée."
        )

        return redirect(
            "/detaiFacture/"
            + str(id_facture)
        )

    df.delete()

    return redirect(
        "/detaiFacture/"
        + str(id_facture)
    )



@login_required(login_url="sign_in")
def addDetailFacture(request):

    # =========================================================
    # VÉRIFIER LA MÉTHODE
    # =========================================================

    if request.method != "POST":
        return redirect("facture")

    # =========================================================
    # RÉCUPÉRER LES DONNÉES
    # =========================================================

    produit_id = request.POST.get("produit")
    facture_id = request.POST.get("facture")
    qte_str = request.POST.get("qte", "").strip()

    # =========================================================
    # VÉRIFIER PRODUIT + FACTURE
    # =========================================================

    if not produit_id or not facture_id:

        messages.error(
            request,
            "Le produit et la facture sont obligatoires."
        )

        return redirect("facture")

    # =========================================================
    # RÉCUPÉRER LA FACTURE
    # =========================================================

    fact = get_object_or_404(
        Facture,
        pk=facture_id
    )

    # =========================================================
    # VÉRIFIER SI LA FACTURE EST DÉJÀ VALIDÉE
    # =========================================================

    if fact.imprimer:

        messages.error(
            request,
            "Cette facture est déjà validée et ne peut plus être modifiée."
        )

        return redirect(
            "/detaiFacture/" + str(fact.id)
        )

    # =========================================================
    # VALIDATION DE LA QUANTITÉ
    # =========================================================

    try:

        qte = Decimal(qte_str)

    except (InvalidOperation, TypeError, ValueError):

        messages.error(
            request,
            "La quantité saisie est invalide."
        )

        return redirect(
            "/detaiFacture/" + str(fact.id)
        )

    if qte <= 0:

        messages.error(
            request,
            "La quantité doit être supérieure à zéro."
        )

        return redirect(
            "/detaiFacture/" + str(fact.id)
        )

    # =========================================================
    # POUR UNE PHARMACIE :
    # LA QUANTITÉ DOIT ÊTRE ENTIÈRE
    # =========================================================

    if qte != qte.to_integral_value():

        messages.error(
            request,
            "La quantité doit être un nombre entier."
        )

        return redirect(
            "/detaiFacture/" + str(fact.id)
        )

    # =========================================================
    # RÉCUPÉRER LE PRODUIT
    # =========================================================

    pro = get_object_or_404(
        Produit,
        pk=produit_id
    )

    # =========================================================
    # VÉRIFIER SI LE PRODUIT EXISTE DÉJÀ
    # =========================================================

    existe = Detail_facture.objects.filter(
        facture=fact,
        produit=pro
    ).exists()

    if existe:

        messages.error(
            request,
            f"Le produit « {pro.nom} » est déjà présent dans cette facture."
        )

        return redirect(
            "/detaiFacture/" + str(fact.id)
        )

    # =========================================================
    # PRIX TTC DU PRODUIT
    #
    # Produit.pu = prix TTC
    # TVA = 16 %
    # =========================================================

    pu_ttc = Decimal(
        pro.pu or "0.00"
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    # =========================================================
    # VÉRIFIER QUE LE PRIX EST VALIDE
    # =========================================================

    if pu_ttc < 0:

        messages.error(
            request,
            "Le prix du produit est invalide."
        )

        return redirect(
            "/detaiFacture/" + str(fact.id)
        )

    # =========================================================
    # CALCUL HT + TVA
    # =========================================================

    taux_tva = TVA_TAUX

    pu_ht, tva_unitaire = calcul_tva_depuis_ttc(
        pu_ttc
    )

    # =========================================================
    # CRÉATION + RECALCUL DANS UNE TRANSACTION
    # =========================================================

    with transaction.atomic():

        # -----------------------------------------------------
        # CRÉER LE DÉTAIL
        # -----------------------------------------------------

        Detail_facture.objects.create(

            facture=fact,

            produit=pro,

            quantite=qte,

            pu_ttc=pu_ttc,

            pu_ht=pu_ht,

            tva_unitaire=tva_unitaire,

            taux_tva=taux_tva,
        )

        # -----------------------------------------------------
        # RÉCUPÉRER TOUS LES DÉTAILS DE LA FACTURE
        # -----------------------------------------------------

        details = Detail_facture.objects.filter(
            facture=fact
        )

        # -----------------------------------------------------
        # INITIALISER LES TOTAUX
        # -----------------------------------------------------

        total_ht = Decimal("0.00")
        total_tva = Decimal("0.00")
        total_ttc = Decimal("0.00")

        # -----------------------------------------------------
        # CALCULER LES TOTAUX
        # -----------------------------------------------------

        for detail in details:

            quantite = detail.quantite or Decimal("0.00")

            pu_ttc_detail = detail.pu_ttc or Decimal("0.00")
            pu_ht_detail = detail.pu_ht or Decimal("0.00")
            tva_detail = detail.tva_unitaire or Decimal("0.00")

            # Total TTC de la ligne
            total_ttc += (
                pu_ttc_detail * quantite
            )

            # Total HT de la ligne
            total_ht += (
                pu_ht_detail * quantite
            )

            # Total TVA de la ligne
            total_tva += (
                tva_detail * quantite
            )

        # -----------------------------------------------------
        # ARRONDIR LES TOTAUX
        # -----------------------------------------------------

        total_ht = total_ht.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        total_tva = total_tva.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        total_ttc = total_ttc.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # SÉCURITÉ :
        # HT + TVA DOIT ÊTRE ÉGAL AU TTC
        # -----------------------------------------------------

        total_ttc = (
            total_ht + total_tva
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # ENREGISTRER LES TOTAUX DANS FACTURE
        # -----------------------------------------------------

        fact.total_ht = total_ht
        fact.total_tva = total_tva
        fact.total_ttc = total_ttc

        fact.save(
            update_fields=[
                "total_ht",
                "total_tva",
                "total_ttc",
                "updatedAt",
            ]
        )

    # =========================================================
    # MESSAGE DE SUCCÈS
    # =========================================================

    messages.success(
        request,
        f"Le produit « {pro.nom} » a été ajouté à la facture."
    )

    # =========================================================
    # RETOUR À LA FACTURE
    # =========================================================

    return redirect(
        "/detaiFacture/" + str(fact.id)
    )

# ==========================================================
# IMPRESSION / VALIDATION FACTURE
# ==========================================================

@login_required(login_url="sign_in")
def print_facture(request, id):

    print("\n")
    print("=" * 100)
    print(">>> DEBUT print_facture()")
    print(">>> Facture ID :", id)
    print(">>> Utilisateur :", request.user)
    print("=" * 100)

    # ============================================================
    # TRANSACTION COMPLETE
    # ============================================================

    with transaction.atomic():

        # ========================================================
        # RECUPERATION + VERROUILLAGE DE LA FACTURE
        # ========================================================

        try:

            sel_facture = (
                Facture.objects
                .select_for_update()
                .get(id=id)
            )

        except Facture.DoesNotExist:

            messages.error(
                request,
                "❌ La facture demandée n'existe pas."
            )

            return redirect(
                "/detaiFacture/" + str(id)
            )

        print(
            ">>> Facture trouvée :",
            sel_facture.id
        )

        # ========================================================
        # VERIFICATION : FACTURE DEJA IMPRIMEE
        # ========================================================

        if sel_facture.imprimer:

            print(
                ">>> FACTURE DEJA IMPRIMEE"
            )

            messages.error(
                request,
                f"❌ La facture #{sel_facture.id} a déjà été "
                f"imprimée et validée. "
                f"Elle ne peut pas être imprimée une deuxième fois."
            )

            return redirect(
                "/detaiFacture/" + str(sel_facture.id)
            )

        # ========================================================
        # RECUPERATION DES DETAILS
        # ========================================================

        details = list(
            Detail_facture.objects
            .select_related("produit")
            .filter(
                facture=sel_facture
            )
        )

        if not details:

            messages.error(
                request,
                "❌ Impossible d'imprimer cette facture : "
                "elle ne contient aucun produit."
            )

            return redirect(
                "/detaiFacture/" + str(sel_facture.id)
            )

        print(
            ">>> Nombre de détails :",
            len(details)
        )

        # ========================================================
        # DATE DU JOUR
        # ========================================================

        aujourd_hui = date.today()

        # ========================================================
        # TOTAUX
        # ========================================================

        total_ht = Decimal("0.00")
        total_tva = Decimal("0.00")
        total_ttc = Decimal("0.00")

        # ========================================================
        # LISTE POUR LE TEMPLATE
        # ========================================================

        list_facture = []

        # ========================================================
        # TRAITEMENT DES DETAILS
        # ========================================================

        for detail in details:

            print("\n")
            print("-" * 100)

            # ====================================================
            # VERIFICATION PRODUIT
            # ====================================================

            if not detail.produit_id:

                messages.error(
                    request,
                    "❌ Un détail de la facture ne possède "
                    "aucun produit."
                )

                return redirect(
                    "/detaiFacture/" + str(sel_facture.id)
                )

            # ====================================================
            # VERROUILLAGE DU PRODUIT
            # ====================================================

            try:

                produit = (
                    Produit.objects
                    .select_for_update()
                    .get(id=detail.produit_id)
                )

            except Produit.DoesNotExist:

                messages.error(
                    request,
                    f"❌ Le produit associé à la facture "
                    f"n'existe plus."
                )

                return redirect(
                    "/detaiFacture/" + str(sel_facture.id)
                )

            print(
                ">>> Produit :",
                produit.nom
            )

            # ====================================================
            # QUANTITE DEMANDEE
            # ====================================================

            try:

                quantite_demandee = Decimal(
                    str(
                        detail.quantite
                        if detail.quantite is not None
                        else "0.00"
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                messages.error(
                    request,
                    f"❌ Quantité invalide pour "
                    f"{produit.nom}."
                )

                return redirect(
                    "/detaiFacture/" + str(sel_facture.id)
                )

            quantite_demandee = (
                quantite_demandee.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            if quantite_demandee <= 0:

                messages.error(
                    request,
                    f"❌ La quantité demandée pour "
                    f"{produit.nom} doit être supérieure à zéro."
                )

                return redirect(
                    "/detaiFacture/" + str(sel_facture.id)
                )

            print(
                ">>> Quantité demandée :",
                quantite_demandee
            )

            # ====================================================
            # STOCK GLOBAL PRODUIT
            # ====================================================

            try:

                stock_global_avant = Decimal(
                    str(
                        produit.quantite
                        if produit.quantite is not None
                        else "0.00"
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                stock_global_avant = Decimal("0.00")

            stock_global_avant = (
                stock_global_avant.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            print(
                ">>> Stock global avant :",
                stock_global_avant
            )

            # ====================================================
            # RECUPERATION DES LOTS
            #
            # FEFO
            # First Expired, First Out
            # ====================================================

            lots = list(
                Lot.objects
                .select_for_update()
                .filter(
                    produit_id=produit.id,
                    quantite__gt=0,
                    date_peremption__gte=aujourd_hui
                )
                .order_by(
                    "date_peremption",
                    "id"
                )
            )

            print(
                ">>> Nombre de lots disponibles :",
                len(lots)
            )

            # ====================================================
            # STOCK TOTAL DES LOTS
            # ====================================================

            stock_lots = Decimal("0.00")

            for lot in lots:

                try:

                    stock_lot = Decimal(
                        str(
                            lot.quantite
                            if lot.quantite is not None
                            else "0.00"
                        )
                    )

                except (
                    InvalidOperation,
                    TypeError,
                    ValueError
                ):

                    stock_lot = Decimal("0.00")

                stock_lot = (
                    stock_lot.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                )

                if stock_lot > 0:

                    stock_lots += stock_lot

            stock_lots = (
                stock_lots.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            print(
                ">>> Stock total des lots :",
                stock_lots
            )

            # ====================================================
            # VERIFICATION STOCK GLOBAL
            # ====================================================

            if stock_global_avant < quantite_demandee:

                messages.error(
                    request,
                    f"❌ Stock insuffisant pour "
                    f"{produit.nom}. "
                    f"Demandé : {quantite_demandee}, "
                    f"stock disponible : {stock_global_avant}."
                )

                return redirect(
                    "/detaiFacture/" + str(sel_facture.id)
                )

            # ====================================================
            # VERIFICATION STOCK DES LOTS
            # ====================================================

            if stock_lots < quantite_demandee:

                messages.error(
                    request,
                    f"❌ Stock insuffisant dans les lots "
                    f"pour {produit.nom}. "
                    f"Demandé : {quantite_demandee}, "
                    f"disponible dans les lots : {stock_lots}."
                )

                return redirect(
                    "/detaiFacture/" + str(sel_facture.id)
                )

            # ====================================================
            # QUANTITE RESTANTE
            # ====================================================

            quantite_restante = quantite_demandee

            # ====================================================
            # STOCK GLOBAL COURANT
            # ====================================================

            stock_global_courant = stock_global_avant

            # ====================================================
            # CONSOMMATION DES LOTS
            # ====================================================

            for lot in lots:

                if quantite_restante <= 0:
                    break

                # =================================================
                # STOCK LOT AVANT
                # =================================================

                try:

                    stock_lot_avant = Decimal(
                        str(
                            lot.quantite
                            if lot.quantite is not None
                            else "0.00"
                        )
                    )

                except (
                    InvalidOperation,
                    TypeError,
                    ValueError
                ):

                    stock_lot_avant = Decimal("0.00")

                stock_lot_avant = (
                    stock_lot_avant.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                )

                if stock_lot_avant <= 0:
                    continue

                # =================================================
                # QUANTITE A SORTIR
                # =================================================

                quantite_a_sortir = min(
                    stock_lot_avant,
                    quantite_restante
                )

                quantite_a_sortir = (
                    quantite_a_sortir.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                )

                if quantite_a_sortir <= 0:
                    continue

                # =================================================
                # STOCK LOT APRES
                # =================================================

                stock_lot_apres = (
                    stock_lot_avant
                    - quantite_a_sortir
                )

                stock_lot_apres = (
                    stock_lot_apres.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                )

                print(
                    f">>> LOT #{lot.id}"
                )

                print(
                    ">>> Péremption :",
                    lot.date_peremption
                )

                print(
                    ">>> Stock lot avant :",
                    stock_lot_avant
                )

                print(
                    ">>> Quantité sortie :",
                    quantite_a_sortir
                )

                print(
                    ">>> Stock lot après :",
                    stock_lot_apres
                )

                # =================================================
                # MISE A JOUR DU LOT
                # =================================================

                lot.quantite = stock_lot_apres

                lot.save(
                    update_fields=[
                        "quantite"
                    ]
                )

                # =================================================
                # CREATION MOUVEMENT STOCK
                # =================================================

                MouvementStock.objects.create(

                    produit=produit,

                    lot=lot,

                    user=request.user,

                    type=MouvementStock.TYPE_SORTIE,

                    quantite=quantite_a_sortir,

                    stock_avant=stock_lot_avant,

                    stock_apres=stock_lot_apres,

                    motif=(
                        f"Vente - Facture "
                        f"#{sel_facture.id}"
                    )
                )

                print(
                    ">>> MouvementStock créé."
                )

                # =================================================
                # QUANTITE RESTANTE
                # =================================================

                quantite_restante -= (
                    quantite_a_sortir
                )

                quantite_restante = (
                    quantite_restante.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                )

                # =================================================
                # STOCK GLOBAL
                # =================================================

                stock_global_courant -= (
                    quantite_a_sortir
                )

                stock_global_courant = (
                    stock_global_courant.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                )

                print(
                    ">>> Quantité restante :",
                    quantite_restante
                )

                print(
                    ">>> Stock global courant :",
                    stock_global_courant
                )

            # ====================================================
            # VERIFICATION FINALE
            # ====================================================

            if quantite_restante > 0:

                raise ValueError(
                    f"Stock insuffisant pour "
                    f"{produit.nom}. "
                    f"Quantité restante : "
                    f"{quantite_restante}"
                )

            # ====================================================
            # SECURITE STOCK GLOBAL
            # ====================================================

            if stock_global_courant < 0:

                stock_global_courant = Decimal(
                    "0.00"
                )

            # ====================================================
            # MISE A JOUR PRODUIT
            # ====================================================

            produit.quantite = stock_global_courant

            produit.save(
                update_fields=[
                    "quantite"
                ]
            )

            print(
                ">>> Stock global après :",
                produit.quantite
            )

            # ====================================================
            # STOCK MINIMUM
            # ====================================================

            try:

                stock_minimum = Decimal(
                    str(
                        getattr(
                            produit,
                            "stock_minimum",
                            "0.00"
                        )
                        or "0.00"
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                stock_minimum = Decimal(
                    "0.00"
                )

            stock_minimum = (
                stock_minimum.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            # ====================================================
            # ALERTE STOCK EPUISE
            # ====================================================

            if stock_global_courant <= 0:

                messages.warning(
                    request,
                    f"⚠️ STOCK ÉPUISÉ : "
                    f"{produit.nom}. "
                    f"Un réapprovisionnement est nécessaire."
                )

            # ====================================================
            # ALERTE STOCK FAIBLE
            # ====================================================

            elif (
                stock_minimum > 0
                and stock_global_courant <= stock_minimum
            ):

                messages.warning(
                    request,
                    f"⚠️ STOCK FAIBLE : "
                    f"{produit.nom}. "
                    f"Stock restant : "
                    f"{stock_global_courant}. "
                    f"Stock minimum : "
                    f"{stock_minimum}. "
                    f"Un réapprovisionnement est recommandé."
                )

            # ====================================================
            # PRIX TTC
            # ====================================================

            try:

                pu_ttc = Decimal(
                    str(
                        detail.pu_ttc
                        if detail.pu_ttc is not None
                        else "0.00"
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                messages.error(
                    request,
                    f"❌ Prix TTC invalide pour "
                    f"{produit.nom}."
                )

                raise ValueError(
                    f"Prix TTC invalide pour {produit.nom}"
                )

            pu_ttc = (
                pu_ttc.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            # ====================================================
            # PRIX HT
            # ====================================================

            try:

                pu_ht = Decimal(
                    str(
                        detail.pu_ht
                        if detail.pu_ht is not None
                        else "0.00"
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                messages.error(
                    request,
                    f"❌ Prix HT invalide pour "
                    f"{produit.nom}."
                )

                raise ValueError(
                    f"Prix HT invalide pour {produit.nom}"
                )

            pu_ht = (
                pu_ht.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            # ====================================================
            # TVA UNITAIRE
            # ====================================================

            try:

                tva_unitaire = Decimal(
                    str(
                        detail.tva_unitaire
                        if detail.tva_unitaire is not None
                        else "0.00"
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                tva_unitaire = Decimal(
                    "0.00"
                )

            tva_unitaire = (
                tva_unitaire.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            # ====================================================
            # TAUX TVA
            # ====================================================

            try:

                taux_tva = Decimal(
                    str(
                        detail.taux_tva
                        if detail.taux_tva is not None
                        else "16.00"
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                taux_tva = Decimal(
                    "16.00"
                )

            taux_tva = (
                taux_tva.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            print(
                ">>> PU HT :",
                pu_ht
            )

            print(
                ">>> PU TTC :",
                pu_ttc
            )

            print(
                ">>> TVA unitaire :",
                tva_unitaire
            )

            print(
                ">>> Taux TVA :",
                taux_tva
            )

            # ====================================================
            # MONTANT HT
            # ====================================================

            montant_ligne_ht = (
                quantite_demandee
                * pu_ht
            )

            montant_ligne_ht = (
                montant_ligne_ht.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            # ====================================================
            # MONTANT TVA
            # ====================================================

            montant_ligne_tva = (
                quantite_demandee
                * tva_unitaire
            )

            montant_ligne_tva = (
                montant_ligne_tva.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            # ====================================================
            # TOTAL TTC
            # ====================================================

            montant_ligne_ttc = (
                quantite_demandee
                * pu_ttc
            )

            montant_ligne_ttc = (
                montant_ligne_ttc.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

            # ====================================================
            # TOTAUX
            # ====================================================

            total_ht += montant_ligne_ht
            total_tva += montant_ligne_tva
            total_ttc += montant_ligne_ttc

            # ====================================================
            # LIGNE POUR LE TEMPLATE
            # ====================================================

            list_facture.append({

                "produit": produit.nom,

                "pu": pu_ttc,

                "qte": quantite_demandee,

                "total": montant_ligne_ttc,
            })

            print(
                ">>> Ligne facture ajoutée :",
                produit.nom,
                "| PU TTC :",
                pu_ttc,
                "| QTE :",
                quantite_demandee,
                "| TOTAL TTC :",
                montant_ligne_ttc
            )

        # ========================================================
        # ARRONDISSEMENT DES TOTAUX
        # ========================================================

        total_ht = (
            total_ht.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
        )

        total_tva = (
            total_tva.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
        )

        total_ttc = (
            total_ttc.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
        )

        print("\n")
        print("=" * 100)
        print(">>> TOTAL HT  :", total_ht)
        print(">>> TOTAL TVA :", total_tva)
        print(">>> TOTAL TTC :", total_ttc)
        print("=" * 100)

        # ========================================================
        # MISE A JOUR FACTURE
        # ========================================================

        sel_facture.imprimer = True

        if hasattr(sel_facture, "total_ht"):
            sel_facture.total_ht = total_ht

        if hasattr(sel_facture, "total_tva"):
            sel_facture.total_tva = total_tva

        if hasattr(sel_facture, "total_ttc"):
            sel_facture.total_ttc = total_ttc

        # Si ton modèle possède seulement "total"
        if hasattr(sel_facture, "total"):
            sel_facture.total = total_ttc

        sel_facture.save()

        print(
            ">>> Facture marquée comme imprimée."
        )

        # ========================================================
        # DONNEES QR CODE
        # ========================================================

        data_liste = {

            "facture": sel_facture.id,

            "numero": getattr(
                sel_facture,
                "numero",
                sel_facture.id
            ),

            "date": str(
                getattr(
                    sel_facture,
                    "date",
                    aujourd_hui
                )
            ),

            "total_ht": str(
                total_ht
            ),

            "total_tva": str(
                total_tva
            ),

            "total_ttc": str(
                total_ttc
            ),
        }

        data_qr = json.dumps(
            data_liste,
            ensure_ascii=False
        )

        print(
            ">>> Données QR :",
            data_qr
        )

        # ========================================================
        # DOSSIER QR
        #
        # MEDIA_ROOT/facture/
        #
        # Exemple :
        # C:/market-app/kivu/mediafiles/facture/
        # ========================================================

        dossier_qr = os.path.join(
            settings.MEDIA_ROOT,
            "mediafiles/facture/",
        )

        os.makedirs(
            dossier_qr,
            exist_ok=True
        )

        # ========================================================
        # NOM QR
        # ========================================================

        nom_qr = (
            f"qr_facture_"
            f"{sel_facture.id}_"
            f"{int(time.time())}.png"
        )

        # ========================================================
        # CHEMIN PHYSIQUE
        # ========================================================

        chemin_qr = os.path.join(
            dossier_qr,
            nom_qr
        )

        # ========================================================
        # GENERATION QR
        # ========================================================

        qr_image = qrcode.make(
            data_qr
        )

        qr_image.save(
            chemin_qr
        )

        print(
            ">>> QR Code enregistré :",
            chemin_qr
        )

        # ========================================================
        # VERIFICATION FICHIER
        # ========================================================

        if os.path.exists(chemin_qr):

            print(
                ">>> ✓ FICHIER QR EXISTE"
            )

            print(
                ">>> Taille QR :",
                os.path.getsize(chemin_qr),
                "octets"
            )

        else:

            print(
                ">>> ❌ ERREUR : QR NON ENREGISTRE"
            )

            raise FileNotFoundError(
                f"Le QR Code n'a pas pu être enregistré : "
                f"{chemin_qr}"
            )

        # ========================================================
        # URL MEDIA DU QR
        # ========================================================

        qr_url = (
            settings.MEDIA_URL
            + "facture/"
            + nom_qr
        )

        print(
            ">>> QR URL :",
            qr_url
        )

        # ========================================================
        # NOM OPERATEUR
        # ========================================================

        noms_operateur = getattr(
            request.user,
            "noms",
            str(request.user)
        )

        # ========================================================
        # CONTEXTE PDF
        # ========================================================

        context = {

            "facture": sel_facture,

            "details": details,

            "list_facture": list_facture,

            "total_ht": total_ht,

            "total_tva": total_tva,

            "total_ttc": total_ttc,

            "sommefac": total_ttc,

            # URL du QR
            "qr_code": qr_url,

            # Nom physique du fichier
            "img": nom_qr,

            "noms": noms_operateur,

            "utilisateur": noms_operateur,

            "date_impression": aujourd_hui,
        }

        print(
            ">>> Nombre de lignes PDF :",
            len(list_facture)
        )

        print(
            ">>> Contexte PDF préparé."
        )

        # ========================================================
        # GENERATION PDF
        # ========================================================

        print(
            ">>> Génération du PDF..."
        )

        pdf = render_to_pdf(
            "facture/facture.html",
            context,
            "facture_" + str(sel_facture.id)
        )

        print(
            ">>> PDF généré avec succès."
        )

        print("=" * 100)
        print(">>> FIN print_facture()")
        print("=" * 100)

        return pdf
# ==========================================================
# RAPPORTS : RECETTES DES FACTURIERS
# ==========================================================

@login_required(login_url="sign_in")
def recettes_facturiers(request):

    maintenant = timezone.localtime(
        timezone.now()
    )

    debut_jour = maintenant.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    debut_mois = debut_jour.replace(
        day=1
    )

    debut_annee = debut_jour.replace(
        month=1,
        day=1
    )

    facturiers = User.objects.filter(
        profile__name__iexact="facturier"
    ).order_by(
        "noms"
    )

    donnees = []

    for user in facturiers:

        # ==================================================
        # FACTURES VALIDÉES DU JOUR
        # ==================================================

        factures_jour_qs = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_jour,
            createdAt__lte=maintenant,
            imprimer=True
        )

        recette_jour_ht = factures_jour_qs.aggregate(
            total=Coalesce(
                Sum("total_ht"),
                Decimal("0.00")
            )
        )["total"]

        recette_jour_tva = factures_jour_qs.aggregate(
            total=Coalesce(
                Sum("total_tva"),
                Decimal("0.00")
            )
        )["total"]

        recette_jour_ttc = factures_jour_qs.aggregate(
            total=Coalesce(
                Sum("total_ttc"),
                Decimal("0.00")
            )
        )["total"]

        # ==================================================
        # FACTURES VALIDÉES DU MOIS
        # ==================================================

        factures_mois_qs = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_mois,
            createdAt__lte=maintenant,
            imprimer=True
        )

        recette_mois_ht = factures_mois_qs.aggregate(
            total=Coalesce(
                Sum("total_ht"),
                Decimal("0.00")
            )
        )["total"]

        recette_mois_tva = factures_mois_qs.aggregate(
            total=Coalesce(
                Sum("total_tva"),
                Decimal("0.00")
            )
        )["total"]

        recette_mois_ttc = factures_mois_qs.aggregate(
            total=Coalesce(
                Sum("total_ttc"),
                Decimal("0.00")
            )
        )["total"]

        # ==================================================
        # FACTURES VALIDÉES DE L'ANNÉE
        # ==================================================

        factures_annee_qs = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_annee,
            createdAt__lte=maintenant,
            imprimer=True
        )

        recette_annee_ht = factures_annee_qs.aggregate(
            total=Coalesce(
                Sum("total_ht"),
                Decimal("0.00")
            )
        )["total"]

        recette_annee_tva = factures_annee_qs.aggregate(
            total=Coalesce(
                Sum("total_tva"),
                Decimal("0.00")
            )
        )["total"]

        recette_annee_ttc = factures_annee_qs.aggregate(
            total=Coalesce(
                Sum("total_ttc"),
                Decimal("0.00")
            )
        )["total"]

        # ==================================================
        # NOMBRE DE FACTURES
        # ==================================================

        factures_jour = factures_jour_qs.count()

        factures_mois = factures_mois_qs.count()

        factures_annee = factures_annee_qs.count()

        donnees.append({

            "user": user,

            # ==========================
            # JOUR
            # ==========================

            "recette_jour": recette_jour_ttc,
            "recette_jour_ht": recette_jour_ht,
            "recette_jour_tva": recette_jour_tva,
            "recette_jour_ttc": recette_jour_ttc,

            "factures_jour": factures_jour,

            # ==========================
            # MOIS
            # ==========================

            "recette_mois": recette_mois_ttc,
            "recette_mois_ht": recette_mois_ht,
            "recette_mois_tva": recette_mois_tva,
            "recette_mois_ttc": recette_mois_ttc,

            "factures_mois": factures_mois,

            # ==========================
            # ANNÉE
            # ==========================

            "recette_annee": recette_annee_ttc,
            "recette_annee_ht": recette_annee_ht,
            "recette_annee_tva": recette_annee_tva,
            "recette_annee_ttc": recette_annee_ttc,

            "factures_annee": factures_annee,
        })

    # ======================================================
    # TOTAUX GÉNÉRAUX DU MOIS
    # ======================================================

    toutes_factures_mois = Facture.objects.filter(
        createdAt__gte=debut_mois,
        createdAt__lte=maintenant,
        imprimer=True
    )

    total_mois_ht = toutes_factures_mois.aggregate(
        total=Coalesce(
            Sum("total_ht"),
            Decimal("0.00")
        )
    )["total"]

    total_mois_tva = toutes_factures_mois.aggregate(
        total=Coalesce(
            Sum("total_tva"),
            Decimal("0.00")
        )
    )["total"]

    total_mois_ttc = toutes_factures_mois.aggregate(
        total=Coalesce(
            Sum("total_ttc"),
            Decimal("0.00")
        )
    )["total"]

    nombre_factures_mois = toutes_factures_mois.count()

    context = {

        "facturiers": donnees,

        "date": maintenant,

        "lrapport": "active",

        # ==================================================
        # RAPPORT GLOBAL
        # ==================================================

        "total_mois_ht": total_mois_ht,

        "total_mois_tva": total_mois_tva,

        "total_mois_ttc": total_mois_ttc,

        "nombre_factures_mois": nombre_factures_mois,

        "taux_tva": TVA_TAUX,
    }

    return render(
        request,
        "facturation/recettes_facturiers.html",
        context
    )


# ==========================================================
# STOCK
# ==========================================================

def ajouter_mois(date_depart, mois):

    mois_total = (
        date_depart.month
        - 1
        + mois
    )

    annee = (
        date_depart.year
        + mois_total // 12
    )

    mois = (
        mois_total % 12
        + 1
    )

    if mois == 12:

        mois_suivant = date(
            annee + 1,
            1,
            1
        )

    else:

        mois_suivant = date(
            annee,
            mois + 1,
            1
        )

    dernier_jour = (
        mois_suivant
        - date.resolution
    ).day

    jour = min(
        date_depart.day,
        dernier_jour
    )

    return date(
        annee,
        mois,
        jour
    )


def statut_peremption(date_peremption):

    aujourd_hui = date.today()

    if date_peremption < aujourd_hui:

        return "perime"

    limite_3_mois = ajouter_mois(
        aujourd_hui,
        3
    )

    limite_4_mois = ajouter_mois(
        aujourd_hui,
        4
    )

    if date_peremption <= limite_3_mois:

        return "rouge"

    if date_peremption <= limite_4_mois:

        return "orange"

    return "vert"


# ==========================================================
# STOCK GÉNÉRAL
# ==========================================================

@login_required
def stock(request):

    # ==============================
    # RECHERCHE
    # ==============================

    rech = request.GET.get(
        "rech",
        ""
    ).strip()

    # ==============================
    # PRODUITS
    # ==============================

    produits = (
        Produit.objects
        .select_related("appartement")
        .prefetch_related("lots")
        .order_by("nom")
    )

    # ==============================
    # FILTRE DE RECHERCHE
    # ==============================

    if rech:

        produits = produits.filter(
            Q(nom__icontains=rech)
            | Q(appartement__nom__icontains=rech)
            | Q(lots__numero__icontains=rech)
        ).distinct()

    # ==============================
    # DATE ACTUELLE
    # ==============================

    aujourd_hui = date.today()

    # ==============================
    # STOCK TOTAL
    # ==============================

    total_stock = (
        Produit.objects.aggregate(
            total=Coalesce(
                Sum("quantite"),
                Decimal("0.00")
            )
        )["total"]
    )

    # ==============================
    # PRODUITS EN STOCK FAIBLE
    # ==============================

    produits_alerte = (
        Produit.objects
        .filter(
            quantite__lte=F("stock_minimum")
        )
        .count()
    )

    # ==============================
    # LOTS PÉRIMÉS
    # ==============================

    lots_perimes = (
        Lot.objects
        .filter(
            quantite__gt=0,
            date_peremption__lt=aujourd_hui
        )
        .count()
    )

    # ==============================
    # VALEUR DU STOCK
    #
    # quantité × prix de vente TTC
    # ==============================

    valeur_stock = Decimal("0.00")

    produits_valeur = Produit.objects.all()

    for produit in produits_valeur:

        quantite = (
            produit.quantite
            or Decimal("0.00")
        )

        prix = (
            produit.pu
            or Decimal("0.00")
        )

        valeur_stock += (
            quantite * prix
        )

    # ==============================
    # CHIFFRE D'AFFAIRES TTC
    # ==============================

    chiffre_affaires = (
        Facture.objects
        .filter(
            imprimer=True
        )
        .aggregate(
            total=Coalesce(
                Sum("total_ttc"),
                Decimal("0.00")
            )
        )["total"]
    )

    # ==============================
    # CHIFFRE D'AFFAIRES HT
    # ==============================

    chiffre_affaires_ht = (
        Facture.objects
        .filter(
            imprimer=True
        )
        .aggregate(
            total=Coalesce(
                Sum("total_ht"),
                Decimal("0.00")
            )
        )["total"]
    )

    # ==============================
    # TVA COLLECTÉE
    # ==============================

    tva_collectee = (
        Facture.objects
        .filter(
            imprimer=True
        )
        .aggregate(
            total=Coalesce(
                Sum("total_tva"),
                Decimal("0.00")
            )
        )["total"]
    )

    # ==============================
    # PRÉPARATION DES DONNÉES
    # ==============================

    donnees = []

    for produit in produits:

        lots_data = []

        for lot in produit.lots.all().order_by(
            "date_peremption"
        ):

            statut = statut_peremption(
                lot.date_peremption
            )

            lots_data.append({
                "lot": lot,
                "statut": statut,
            })

        donnees.append({
            "produit": produit,
            "lots": lots_data,
        })

    # ==============================
    # PAGINATION
    # ==============================

    paginator = Paginator(
        donnees,
        12
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    # ==============================
    # RENDU
    # ==============================

    return render(
        request,
        "stock/index.html",
        {
            "page_obj": page_obj,

            "donnees": page_obj.object_list,

            "rech": rech,

            # ======================
            # STATISTIQUES STOCK
            # ======================

            "total_stock": total_stock,

            "valeur_stock": valeur_stock,

            "produits_alerte": produits_alerte,

            "lots_perimes": lots_perimes,
            "lstock": "active",

            # ======================
            # CHIFFRE D'AFFAIRES
            # ======================

            "chiffre_affaires": chiffre_affaires,

            "chiffre_affaires_ht": chiffre_affaires_ht,

            "tva_collectee": tva_collectee,

            "taux_tva": TVA_TAUX,
        }
    )


# ==========================================================
# ENTRÉE STOCK
# ==========================================================

@login_required(login_url="sign_in")
def entree_stock(request):

    produits = Produit.objects.order_by(
        "nom"
    )

    if request.method == "POST":

        produit_id = request.POST.get(
            "produit"
        )

        numero = request.POST.get(
            "numero",
            ""
        ).strip()

        quantite = request.POST.get(
            "quantite"
        )

        date_peremption = request.POST.get(
            "date_peremption"
        )

        motif = request.POST.get(
            "motif",
            ""
        ).strip()

        if (
            not produit_id
            or not quantite
            or not date_peremption
        ):

            messages.error(
                request,
                "Veuillez remplir tous les champs obligatoires."
            )

            return redirect(
                "entree_stock"
            )

        try:

            quantite = Decimal(
                quantite
            )

            if quantite <= 0:

                raise ValueError

        except (
            InvalidOperation,
            ValueError,
            TypeError
        ):

            messages.error(
                request,
                "La quantité doit être supérieure à zéro."
            )

            return redirect(
                "entree_stock"
            )

        try:

            date_peremption_obj = date.fromisoformat(
                date_peremption
            )

        except ValueError:

            messages.error(
                request,
                "La date de péremption est invalide."
            )

            return redirect(
                "entree_stock"
            )

        if date_peremption_obj < date.today():

            messages.error(
                request,
                "La date de péremption ne peut pas être dépassée."
            )

            return redirect(
                "entree_stock"
            )

        produit = get_object_or_404(
            Produit,
            id=produit_id
        )

        with transaction.atomic():

            produit = Produit.objects.select_for_update().get(
                id=produit.id
            )

            stock_avant = (
                produit.quantite
                or Decimal("0")
            )

            lot = Lot.objects.create(
                produit=produit,
                numero=numero or None,
                quantite=quantite,
                date_peremption=date_peremption_obj
            )

            stock_apres = (
                stock_avant
                + quantite
            )

            produit.quantite = stock_apres

            produit.save(
                update_fields=[
                    "quantite"
                ]
            )

            MouvementStock.objects.create(
                produit=produit,
                lot=lot,
                user=request.user,
                type=MouvementStock.TYPE_ENTREE,
                quantite=quantite,
                stock_avant=stock_avant,
                stock_apres=stock_apres,
                motif=(
                    motif
                    or "Entrée de stock"
                )
            )

        messages.success(
            request,
            f"Entrée de {quantite} unité(s) enregistrée avec succès."
        )

        return redirect(
            "stock"
        )

    context = {
        "produits": produits,
        "lentree": "active",
    }

    return render(
        request,
        "stock/entree.html",
        context
    )


# ==========================================================
# SORTIE STOCK
# ==========================================================

@login_required(login_url="sign_in")
def sortie_stock(request):

    produits = Produit.objects.order_by(
        "nom"
    )

    if request.method == "POST":

        produit_id = request.POST.get(
            "produit"
        )

        quantite = request.POST.get(
            "quantite"
        )

        motif = request.POST.get(
            "motif",
            ""
        ).strip()

        if not produit_id or not quantite:

            messages.error(
                request,
                "Veuillez remplir les champs obligatoires."
            )

            return redirect(
                "sortie_stock"
            )

        try:

            quantite = Decimal(
                quantite
            )

            if quantite <= 0:

                raise ValueError

        except (
            InvalidOperation,
            ValueError,
            TypeError
        ):

            messages.error(
                request,
                "La quantité doit être supérieure à zéro."
            )

            return redirect(
                "sortie_stock"
            )

        produit = get_object_or_404(
            Produit,
            id=produit_id
        )

        with transaction.atomic():

            produit = Produit.objects.select_for_update().get(
                id=produit.id
            )

            stock_total = (
                produit.quantite
                or Decimal("0")
            )

            if quantite > stock_total:

                messages.error(
                    request,
                    f"Stock insuffisant. "
                    f"Stock disponible : {stock_total}."
                )

                return redirect(
                    "sortie_stock"
                )

            quantite_restante = quantite

            lots = Lot.objects.select_for_update().filter(
                produit=produit,
                quantite__gt=0
            ).order_by(
                "date_peremption",
                "id"
            )

            stock_courant = stock_total

            for lot in lots:

                if quantite_restante <= 0:

                    break

                stock_avant = stock_courant

                quantite_lot = min(
                    lot.quantite,
                    quantite_restante
                )

                lot.quantite -= quantite_lot

                lot.save(
                    update_fields=[
                        "quantite"
                    ]
                )

                stock_courant -= quantite_lot

                quantite_restante -= quantite_lot

                MouvementStock.objects.create(
                    produit=produit,
                    lot=lot,
                    user=request.user,
                    type=MouvementStock.TYPE_SORTIE,
                    quantite=quantite_lot,
                    stock_avant=stock_avant,
                    stock_apres=stock_courant,
                    motif=(
                        motif
                        or "Sortie de stock"
                    )
                )

            if quantite_restante > 0:

                messages.error(
                    request,
                    f"Stock insuffisant dans les lots pour "
                    f"{produit.nom}."
                )

                return redirect(
                    "sortie_stock"
                )

            produit.quantite = stock_courant

            produit.save(
                update_fields=[
                    "quantite"
                ]
            )

        messages.success(
            request,
            f"Sortie de {quantite} unité(s) enregistrée avec succès."
        )

        return redirect(
            "stock"
        )

    context = {
        "produits": produits,
        "lsortie": "active",
    }

    return render(
        request,
        "stock/sortie.html",
        context
    )


# ==========================================================
# MOUVEMENTS STOCK
# ==========================================================

@login_required(login_url="sign_in")
def mouvements_stock(request):

    rech = request.GET.get(
        "rech",
        ""
    ).strip()

    mouvements = (
        MouvementStock.objects
        .select_related(
            "produit",
            "lot",
            "user",
        )
        .order_by(
            "-createdAt",
            "-id"
        )
    )

    if rech:

        mouvements = mouvements.filter(
            Q(produit__nom__icontains=rech)
            | Q(lot__numero__icontains=rech)
            | Q(type__icontains=rech)
            | Q(user__username__icontains=rech)
            | Q(user__noms__icontains=rech)
            | Q(motif__icontains=rech)
        ).distinct()

    paginator = Paginator(
        mouvements,
        50
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    context = {
        "mouvements": page_obj.object_list,
        "page_obj": page_obj,
        "total_mouvements": paginator.count,
        "rech": rech,
        "lmouvements": "active",
    }

    return render(
        request,
        "stock/mouvements.html",
        context
    )


# ==========================================================
# PRODUITS PROCHES DE LA PÉREMPTION
# ==========================================================

@login_required
def produits_peremption(request):

    aujourd_hui = date.today()

    limite_4_mois = (
        aujourd_hui
        + datetime.timedelta(days=120)
    )

    # ==============================
    # RECHERCHE
    # ==============================

    rech = request.GET.get(
        "rech",
        ""
    ).strip()

    # ==============================
    # LOTS ARRIVANT À EXPIRATION
    # ==============================

    lots = Lot.objects.select_related(
        "produit",
        "produit__appartement"
    ).filter(
        quantite__gt=0,
        date_peremption__lte=limite_4_mois
    )

    # ==============================
    # FILTRE DE RECHERCHE
    # ==============================

    if rech:

        lots = lots.filter(
            Q(produit__nom__icontains=rech)
            | Q(produit__appartement__nom__icontains=rech)
            | Q(numero__icontains=rech)
        )

    # ==============================
    # TRI
    # ==============================

    lots = lots.order_by(
        "date_peremption",
        "produit__nom",
        "id"
    )

    # ==============================
    # STATISTIQUES
    # ==============================

    total_peremption = lots.count()

    total_perimes = lots.filter(
        date_peremption__lt=aujourd_hui
    ).count()

    # ==============================
    # PRÉPARATION DES DONNÉES
    # ==============================

    donnees = []

    for lot in lots:

        jours_restants = (
            lot.date_peremption
            - aujourd_hui
        ).days

        if jours_restants < 0:

            classe = "perime"

        elif jours_restants <= 90:

            classe = "urgent"

        else:

            classe = "surveiller"

        donnees.append({
            "lot": lot,
            "produit": lot.produit,
            "appartement": lot.produit.appartement,
            "date_peremption": lot.date_peremption,
            "jours_restants": jours_restants,
            "classe": classe,
        })

    # ==============================
    # PAGINATION
    # ==============================

    paginator = Paginator(
        donnees,
        50
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    # ==============================
    # RENDU
    # ==============================

    return render(
        request,
        "stock/peremption.html",
        {
            "produits_peremption": page_obj.object_list,
            "page_obj": page_obj,
            "total_peremption": total_peremption,
            "total_perimes": total_perimes,
            "rech": rech,
            "lperemption": "active",
        }
    )
    
    

# ==========================================================
# RAPPORT MENSUEL DES VENTES ET DE LA TVA
# ==========================================================

@login_required(login_url="sign_in")
def rapport_mensuel_tva(request):
    """
    Génère le rapport mensuel des ventes et de la TVA collectée.

    Paramètres GET :
        mois  = 1 à 12
        annee = année

    Exemple :
        /rapport-mensuel-tva/?mois=8&annee=2026
    """

    # ======================================================
    # MOIS / ANNÉE
    # ======================================================

    aujourd_hui = timezone.localdate()

    try:
        mois = int(
            request.GET.get(
                "mois",
                aujourd_hui.month
            )
        )
    except (TypeError, ValueError):
        mois = aujourd_hui.month

    try:
        annee = int(
            request.GET.get(
                "annee",
                aujourd_hui.year
            )
        )
    except (TypeError, ValueError):
        annee = aujourd_hui.year

    # Sécurité
    if mois < 1 or mois > 12:
        mois = aujourd_hui.month

    if annee < 2000 or annee > 2100:
        annee = aujourd_hui.year

    # ======================================================
    # NOMS DES MOIS
    # ======================================================

    noms_mois = [
        "",
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]

    nom_mois = noms_mois[mois]

    # ======================================================
    # FACTURES VALIDÉES DU MOIS
    # ======================================================

    factures = Facture.objects.filter(
        createdAt__year=annee,
        createdAt__month=mois,
        imprimer=True
    ).select_related(
        "user"
    ).order_by(
        "createdAt"
    )

    # ======================================================
    # NOMBRE DE FACTURES
    # ======================================================

    nombre_factures = factures.count()

    # ======================================================
    # TOTAL HT
    # ======================================================

    total_ht = factures.aggregate(
        total=Coalesce(
            Sum("total_ht"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # TOTAL TVA
    # ======================================================

    total_tva = factures.aggregate(
        total=Coalesce(
            Sum("total_tva"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # TOTAL TTC
    # ======================================================

    total_ttc = factures.aggregate(
        total=Coalesce(
            Sum("total_ttc"),
            Decimal("0.00")
        )
    )["total"]

    # ======================================================
    # ARRONDIS
    # ======================================================

    total_ht = (
        total_ht or Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    total_tva = (
        total_tva or Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    total_ttc = (
        total_ttc or Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    # ======================================================
    # VÉRIFICATION
    # HT + TVA = TTC
    # ======================================================

    difference = (
        total_ht + total_tva - total_ttc
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    # ======================================================
    # DÉTAIL DE LA TVA PAR TAUX
    # ======================================================

    details = Detail_facture.objects.filter(
        facture__in=factures
    ).values(
        "taux_tva"
    ).annotate(
        base_ht=Coalesce(
            Sum(
                F("pu_ht") * F("quantite")
            ),
            Decimal("0.00")
        ),
        montant_tva=Coalesce(
            Sum(
                F("tva_unitaire") * F("quantite")
            ),
            Decimal("0.00")
        ),
        montant_ttc=Coalesce(
            Sum(
                F("pu_ttc") * F("quantite")
            ),
            Decimal("0.00")
        ),
        quantite=Coalesce(
            Sum("quantite"),
            Decimal("0.00")
        )
    ).order_by(
        "taux_tva"
    )

    # ======================================================
    # PRÉPARER LES DONNÉES TVA
    # ======================================================

    tva_par_taux = []

    for ligne in details:

        taux = (
            ligne["taux_tva"]
            or Decimal("0.00")
        )

        base_ht = (
            ligne["base_ht"]
            or Decimal("0.00")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        montant_tva = (
            ligne["montant_tva"]
            or Decimal("0.00")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        montant_ttc = (
            ligne["montant_ttc"]
            or Decimal("0.00")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        quantite = (
            ligne["quantite"]
            or Decimal("0.00")
        )

        tva_par_taux.append({
            "taux": taux,
            "base_ht": base_ht,
            "montant_tva": montant_tva,
            "montant_ttc": montant_ttc,
            "quantite": quantite,
        })

    # ======================================================
    # DÉTAIL DES VENTES
    # ======================================================

    lignes_vente = []

    details_vente = Detail_facture.objects.filter(
        facture__in=factures
    ).select_related(
        "facture",
        "produit"
    ).order_by(
        "facture__createdAt",
        "id"
    )

    for detail in details_vente:

        quantite = (
            detail.quantite
            or Decimal("0.00")
        )

        pu_ht = (
            detail.pu_ht
            or Decimal("0.00")
        )

        pu_ttc = (
            detail.pu_ttc
            or Decimal("0.00")
        )

        tva_unitaire = (
            detail.tva_unitaire
            or Decimal("0.00")
        )

        total_ligne_ht = (
            pu_ht * quantite
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        total_ligne_tva = (
            tva_unitaire * quantite
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        total_ligne_ttc = (
            pu_ttc * quantite
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        lignes_vente.append({
            "facture": detail.facture,
            "produit": detail.produit,
            "quantite": quantite,
            "pu_ht": pu_ht,
            "pu_ttc": pu_ttc,
            "taux_tva": detail.taux_tva,
            "total_ht": total_ligne_ht,
            "total_tva": total_ligne_tva,
            "total_ttc": total_ligne_ttc,
        })

    # ======================================================
    # RAPPORT
    # ======================================================

    context = {

        # --------------------------------------------------
        # Identification
        # --------------------------------------------------

        "entreprise": "Kivu SuperMarket",
        "titre": "Rapport mensuel des ventes et de la TVA collectée",

        # --------------------------------------------------
        # Période
        # --------------------------------------------------

        "mois": mois,
        "annee": annee,
        "nom_mois": nom_mois,

        # --------------------------------------------------
        # Statistiques
        # --------------------------------------------------

        "nombre_factures": nombre_factures,

        "total_ht": total_ht,
        "total_tva": total_tva,
        "total_ttc": total_ttc,

        # --------------------------------------------------
        # Contrôle
        # --------------------------------------------------

        "difference": difference,

        # --------------------------------------------------
        # TVA
        # --------------------------------------------------

        "tva_par_taux": tva_par_taux,

        # --------------------------------------------------
        # Ventes
        # --------------------------------------------------

        "lignes_vente": lignes_vente,

        # --------------------------------------------------
        # Factures
        # --------------------------------------------------

        "factures": factures,

        # --------------------------------------------------
        # Utilisateur
        # --------------------------------------------------

        "noms": request.user.noms,
        "profile": getattr(
            request.user,
            "profile",
            None
        ),

        # --------------------------------------------------
        # Menu actif
        # --------------------------------------------------

        "lrapport": "active",

        # --------------------------------------------------
        # Date génération
        # --------------------------------------------------

        "date_generation": timezone.localtime(),

    }

    # ======================================================
    # GÉNÉRATION PDF
    # ======================================================

    return render_to_pdf(
        "rapports/rapport_mensuel_tva.html",
        context
    )


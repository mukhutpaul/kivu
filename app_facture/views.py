
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect


from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout

from django.contrib import messages

from django.db import transaction
from django.db.models import Sum, Avg, Count, Q,F
from django.db.models.functions import Coalesce

from django.utils import timezone

from decimal import Decimal

from datetime import date
import datetime
import qrcode
from time import time
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
# HOME
# ==========================================================

@login_required(login_url="sign_in")
def home(request):

    ap = Appartement.objects.all()

    nbrp = Produit.objects.all().count()

    mois = datetime.date.today().month
    annee = datetime.date.today().year

    totalFacture = Facture.objects.filter(
        createdAt__date=datetime.date.today()
    ).count()

    totalFactureM = Facture.objects.filter(
        createdAt__date__month=mois,
        createdAt__date__year=annee
    ).count()

    totalFactureA = Facture.objects.filter(
        createdAt__date__year=annee
    ).count()

    factj = Facture.objects.filter(
        createdAt__date=datetime.date.today()
    )

    factm = Facture.objects.filter(
        createdAt__date__month=mois,
        createdAt__date__year=annee
    )

    factan = Facture.objects.filter(
        createdAt__date__year=annee
    )

    somme = Decimal("0.00")

    for f in factj:

        factd = Detail_facture.objects.filter(
            facture_id=f.id
        )

        for fd in factd:

            somme += fd.produit.pu * fd.quantite

    sommeMois = Decimal("0.00")

    for f in factm:

        factd = Detail_facture.objects.filter(
            facture_id=f.id
        )

        for fd in factd:

            sommeMois += fd.produit.pu * fd.quantite

    sommeAn = Decimal("0.00")

    for f in factan:

        factd = Detail_facture.objects.filter(
            facture_id=f.id
        )

        for fd in factd:

            sommeAn += fd.produit.pu * fd.quantite

    nbrFemme = 0

    ctx = {
        "hm": "active",
        "totalFacture": totalFacture,
        "sommeMois": sommeMois,
        "somme": somme,
        "nbrp": nbrp,
        "totalFactureM": totalFactureM,
        "totalFactureA": totalFactureA,
        "sommeAn": sommeAn,
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

            except (ValueError, TypeError):

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

            except (ValueError, TypeError):

                msg = "Prix doit être un numérique"

            else:

                apr = Appartement.objects.get(
                    pk=appartement
                )

                pr.nom = nom.upper()
                pr.appartement = apr
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
        )

        centre = request.POST.get(
            "centre",
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

        password = request.POST.get(
            "password",
            ""
        )

        if email == "":

            msg = "Veuillez remplir le mail"

        elif profile == "":

            msg = "Veuillez choisir le profile"

        elif centre == "":

            msg = "Veuillez choisir le centre"

        elif User.objects.filter(
            username=username
        ).exists():

            msg = "Ce nom utilisateur existe déjà"

        elif User.objects.filter(
            email=email
        ).exists():

            msg = "Cette adresse mail existe déjà"

        elif noms == "":

            msg = "Veuillez remplir les noms"

        elif username == "":

            msg = "Veuillez remplir le nom utilisateur"

        elif password == "":

            msg = "Veuillez remplir le mot de passe"

        else:

            pro = Profile.objects.get(
                pk=profile
            )

            u = User(
                noms=noms.upper(),
                profile=pro,
                username=username.upper(),
                email=email,
                is_active=True
            )

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

    if request.user.profile.id == 3:

        factj = Facture.objects.filter(
            createdAt__date=datej,
            user=request.user
        )

        queryset = Facture.objects.filter(
            user=request.user
        )

    else:

        factj = Facture.objects.filter(
            createdAt__date=datej
        )

        queryset = Facture.objects.all()

    nbr = factj.count()

    somme = Decimal("0.00")

    for f in factj:

        factd = Detail_facture.objects.filter(
            facture_id=f.id
        )

        for fd in factd:

            somme += fd.produit.pu * fd.quantite

    if recherche:

        queryset = queryset.filter(
            id__icontains=recherche
        )

    queryset = queryset.order_by(
        "-id"
    )

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

    ctx = {
        "compte": compte,
        "facture": pages,
        "lfact": "active",
        "somme": somme,
        "facture_total_jour": nbr,
        "noms": request.user.noms,
        "profile": request.user.profile,
        "pages": pages,
        "page_obj": pages,
        "recherche": recherche,
    }

    return render(
        request,
        "pages/facture.html",
        ctx
    )


@login_required(login_url="sign_in")
def addFacture(request):

    userId = User.objects.get(
        pk=request.user.id
    )

    f = Facture(
        user=userId
    )

    f.save()

    return HttpResponseRedirect(
        "/facture/"
    )


# ==========================================================
# DETAILS FACTURE
# ==========================================================

@login_required(login_url="sign_in")
def detaiFacture(request, id):

    sel_facture = Facture.objects.get(
        id=id
    )

    liste_produit = Produit.objects.all()

    total = 0

    data_liste = []

    data_produit = []

    sommefac = Decimal("0.00")

    for lp in liste_produit:

        list_sans_fac = Detail_facture.objects.filter(
            facture_id=sel_facture.id,
            produit_id=lp.id
        )

        if not list_sans_fac.exists():

            data_produit.append({
                "id": lp.id,
                "nom": lp.nom
            })

    recherche = request.GET.get(
        "q",
        request.POST.get("rech", "")
    ).strip()

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

    for t in list_facture:

        total_ligne = (
            t.produit.pu
            * t.quantite
        )

        sommefac += total_ligne

        data_liste.append({
            "id": t.id,
            "produit": t.produit,
            "pu": t.produit.pu,
            "qte": t.quantite,
            "total": total_ligne
        })

    ctx = {
        "sel_facture": sel_facture,
        "list_facture": data_liste,
        "Llist_facture": "active",
        "liste_produit": data_produit,
        "sommefac": sommefac,
        "compte": compte,
        "total": total,
        "pages": list_facture,
        "page_obj": list_facture,
        "recherche": recherche,
    }

    return render(
        request,
        "pages/detailFacture.html",
        ctx
    )


@login_required(login_url="sign_in")
def deletedetailFacture(request, id):

    df = Detail_facture.objects.get(
        pk=id
    )

    dt = Facture.objects.get(
        pk=df.facture.id
    )

    id_facture = dt.id

    if dt.imprimer:

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

    if request.method == "POST":

        produit = request.POST.get(
            "produit",
            None
        )

        qte = request.POST.get(
            "qte",
            0
        )

        facture = request.POST.get(
            "facture",
            None
        )

        pro = Produit.objects.get(
            pk=produit
        )

        fact = Facture.objects.get(
            pk=facture
        )

        pr = Detail_facture(
            produit=pro,
            facture=fact,
            quantite=qte
        )

        pr.save()

        return HttpResponseRedirect(
            "/detaiFacture/"
            + str(facture)
        )

    return redirect(
        "facture"
    )


# ==========================================================
# IMPRESSION / VALIDATION FACTURE
# ==========================================================

@login_required(login_url="sign_in")
def print_facture(request, id):

    sel_facture = Facture.objects.get(
        id=id
    )

    # ======================================================
    # FACTURE DÉJÀ VALIDÉE
    # ======================================================

    if sel_facture.imprimer:

        messages.warning(
            request,
            "Cette facture a déjà été validée et le stock a déjà été déduit."
        )

        return redirect(
            "/detaiFacture/"
            + str(sel_facture.id)
        )

    liste_produit = Produit.objects.all()

    total = 0

    data_liste = []

    data_produit = []

    sommefac = Decimal("0.00")

    # ======================================================
    # DÉTAILS
    # ======================================================

    details = Detail_facture.objects.filter(
        facture_id=sel_facture.id
    ).select_related(
        "produit"
    )

    # ======================================================
    # PRODUITS NON PRÉSENTS DANS LA FACTURE
    # ======================================================

    for lp in liste_produit:

        list_sans_fac = Detail_facture.objects.filter(
            facture_id=sel_facture.id,
            produit_id=lp.id
        )

        if not list_sans_fac.exists():

            data_produit.append({
                "id": lp.id,
                "nom": lp.nom
            })

    # ======================================================
    # CALCUL FACTURE
    # ======================================================

    for t in details:

        total_ligne = (
            t.produit.pu
            * t.quantite
        )

        sommefac += total_ligne

        data_liste.append({
            "id": t.id,
            "produit": t.produit,
            "pu": t.produit.pu,
            "qte": t.quantite,
            "total": total_ligne
        })

    # ======================================================
    # TRANSACTION STOCK
    # ======================================================

    with transaction.atomic():

        produits_ids = [
            detail.produit_id
            for detail in details
        ]

        produits_verrouilles = {
            produit.id: produit
            for produit in Produit.objects.select_for_update().filter(
                id__in=produits_ids
            )
        }

        # ==================================================
        # VÉRIFICATION STOCK
        # ==================================================

        for detail in details:

            produit = produits_verrouilles[
                detail.produit_id
            ]

            stock_disponible = (
                produit.quantite
                or Decimal("0")
            )

            if detail.quantite > stock_disponible:

                messages.error(
                    request,
                    f"Stock insuffisant pour {produit.nom}. "
                    f"Disponible : {stock_disponible}, "
                    f"demandé : {detail.quantite}."
                )

                return redirect(
                    "/detaiFacture/"
                    + str(sel_facture.id)
                )

        # ==================================================
        # FEFO
        # ==================================================

        for detail in details:

            produit = produits_verrouilles[
                detail.produit_id
            ]

            quantite_restante = Decimal(
                detail.quantite
            )

            stock_courant = (
                produit.quantite
                or Decimal("0")
            )

            lots = Lot.objects.select_for_update().filter(
                produit=produit,
                quantite__gt=0,
                date_peremption__gte=date.today()
            ).order_by(
                "date_peremption",
                "id"
            )

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
                        f"Vente - Facture #{sel_facture.id}"
                    )
                )

            if quantite_restante > 0:

                messages.error(
                    request,
                    f"Stock insuffisant dans les lots pour "
                    f"{produit.nom}."
                )

                raise Exception(
                    "Stock insuffisant dans les lots."
                )

            produit.quantite = stock_courant

            produit.save(
                update_fields=[
                    "quantite"
                ]
            )

        # ==================================================
        # VALIDATION FACTURE
        # ==================================================

        sel_facture.imprimer = True

        sel_facture.total = sommefac

        sel_facture.save(
            update_fields=[
                "imprimer",
                "total"
            ]
        )

    # ======================================================
    # QR CODE
    # ======================================================

    img = qrcode.make(
        str(data_liste)
    )

    img_name = (
        "facture"
        + str(time())
        + ".png"
    )

    img.save(
        "mediafiles/facture/"
        + img_name
    )

    # ======================================================
    # PDF
    # ======================================================

    ctx = {
        "sel_facture": sel_facture,
        "list_facture": data_liste,
        "Llist_facture": "active",
        "liste_produit": data_produit,
        "sommefac": sommefac,
        "compte": len(details),
        "total": total,
        "img": img_name,
        "produit": data_liste,
        "noms": request.user.noms
    }

    pdf = render_to_pdf(
        "facture/facture.html",
        ctx,
        200
    )

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

        recette_jour = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_jour,
            createdAt__lte=maintenant
        ).aggregate(
            total=Coalesce(
                Sum("total"),
                Decimal("0.00")
            )
        )["total"]

        recette_mois = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_mois,
            createdAt__lte=maintenant
        ).aggregate(
            total=Coalesce(
                Sum("total"),
                Decimal("0.00")
            )
        )["total"]

        recette_annee = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_annee,
            createdAt__lte=maintenant
        ).aggregate(
            total=Coalesce(
                Sum("total"),
                Decimal("0.00")
            )
        )["total"]

        factures_jour = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_jour,
            createdAt__lte=maintenant
        ).count()

        factures_mois = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_mois,
            createdAt__lte=maintenant
        ).count()

        factures_annee = Facture.objects.filter(
            user=user,
            createdAt__gte=debut_annee,
            createdAt__lte=maintenant
        ).count()

        donnees.append({
            "user": user,
            "recette_jour": recette_jour,
            "recette_mois": recette_mois,
            "recette_annee": recette_annee,
            "factures_jour": factures_jour,
            "factures_mois": factures_mois,
            "factures_annee": factures_annee,
        })

    context = {
        "facturiers": donnees,
        "date": maintenant,
        "lrapport": "active",
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
    rech = request.GET.get("rech", "").strip()

    # ==============================
    # PRODUITS
    # ==============================
    produits = Produit.objects.select_related(
        "appartement"
    ).prefetch_related(
        "lots"
    ).order_by("nom")

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
    # STATISTIQUES GÉNÉRALES
    # ==============================
    total_stock = Produit.objects.aggregate(
        total=Sum("quantite")
    )["total"] or Decimal("0")

    produits_alerte = Produit.objects.filter(
        quantite__lte=F("stock_minimum")
    ).count()

    aujourd_hui = date.today()

    lots_perimes = Lot.objects.filter(
        quantite__gt=0,
        date_peremption__lt=aujourd_hui
    ).count()

    # ==============================
    # PRÉPARATION DES DONNÉES
    # ==============================
    donnees = []

    for produit in produits:

        lots_data = []

        for lot in produit.lots.all().order_by("date_peremption"):

            statut = statut_peremption(lot.date_peremption)

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
    paginator = Paginator(donnees, 12)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

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

            "total_stock": total_stock,
            "produits_alerte": produits_alerte,
            "lots_perimes": lots_perimes,
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

    rech = request.GET.get("rech", "").strip()

    mouvements = (
        MouvementStock.objects
        .select_related(
            "produit",
            "lot",
            "user",
        )
        .order_by("-createdAt", "-id")
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

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(
        page_number
    )

    context = {
        "mouvements": page_obj.object_list,
        "page_obj": page_obj,
        "total_mouvements": paginator.count,
        "rech": rech,
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
    limite_4_mois = aujourd_hui + datetime.timedelta(days=120)

    # ==============================
    # RECHERCHE
    # ==============================
    rech = request.GET.get("rech", "").strip()

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
            lot.date_peremption - aujourd_hui
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
    paginator = Paginator(donnees, 50)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

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
        }
    )
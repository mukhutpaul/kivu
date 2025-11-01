from django.shortcuts import render

from app_facture.models.appartement import Appartement
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from app_facture.models.produit import Produit

# Create your views here.
def home(request):
    nbrhomme = 0
    nbrFemme = 0

    ctx ={
        'hm':'active',
        'nbrhomme':nbrhomme,
        'nbrFemme':nbrFemme,
    }
    
    return render(request,"pages/home.html",ctx)

def facture(request):
    nbrhomme = 0
    nbrFemme = 0

    ctx ={
        'lfact':'active',
        'nbrhomme':nbrhomme,
        'nbrFemme':nbrFemme,
    }
    
    return render(request,"pages/facture.html",ctx)


#APPARTEMENT
def appartement(request):
    appartement = Appartement.objects.all()
    
    if request.method == "POST":
        rech = request.POST['rech']
        p = Paginator(Appartement.objects.filter(nom__contains=rech),4)
        page = request.GET.get('page')
        pages =p.get_page(page)
        compte = len(pages)
        if rech == '':
             compte = len(Appartement.objects.all())   
    else:
        p = Paginator(Appartement.objects.all().order_by('-id'), 4)
        page = request.GET.get('page')
        pages =p.get_page(page)
        compte = len(Appartement.objects.all())
    ctx = {
        'compte' : compte,
        'appartement' : pages,
        'lapr': 'active',
        'pages':pages
    }
    
    return render(request,"pages/appartement.html",ctx)


def fAppartement(request):
    nbrhomme = 0
    nbrFemme = 0

    ctx ={
        'lfact':'active',
        'nbrhomme':nbrhomme,
        'nbrFemme':nbrFemme,
    }
    
    return render(request,"formulaires/appartement.html",ctx)


def addAppartement(request):
    p = Paginator(Appartement.objects.all().order_by('-id'), 4)
    page = request.GET.get('page')
    pages =p.get_page(page)
    compte = len(Appartement.objects.all())
    if request.method == 'POST':
        msg = None
        msok = None
        nom = request.POST.get("nom",None)
 
        if nom == '':
            msg ="Veuillez remplir le nom"
        else:
            ap = Appartement(
                nom = nom.upper(),
            )
            ap.save()
            msok = "Opération réussie"
            return HttpResponseRedirect('/appartement/')
        
    ctx ={
        'msg':msg,
        'msok': msok,
        'compte' : compte,
        'appartement' : pages,
        'lapr': 'active',
        'pages':pages
    }
    return render(request,'formulaires/appartement.html',ctx)

def modAppartement(request,id):
    ap= Appartement.objects.get(pk=id)
    
    ctx ={
        'ap': ap
    }
    return render(request,'formulaires/modAppartement.html',ctx)

def updateAppartement(request,id):
    appar= Appartement.objects.get(pk=id)
    if request.method == 'POST':
        msg = None
        msok =None
        
        nom = request.POST.get("nom",None)
     
     
        if nom == '':
            msg ="Veuillez remplir le nom"
        else: 
           appar.nom = nom.upper()
           
           appar.save()
           msok = nom +" modifié avec succès"
           return HttpResponseRedirect('/appartement/')
    ctx ={
        'msg':msg,
        'msok': msok 
    }
    return render(request,'formulaires/modAppartement.html',ctx)

def deleteAppartement(request,id):
    p = Appartement.objects.get(pk=id)
    p.delete()
    return HttpResponseRedirect('/appartement/')

#####################################################
#PRODUITS
#####################################################

#PRODUIT
def produit(request):
    produit = Produit.objects.all()
    
    if request.method == "POST":
        rech = request.POST['rech']
        p = Paginator(Produit.objects.filter(nom__contains=rech),20)
        page = request.GET.get('page')
        pages =p.get_page(page)
        compte = len(pages)
        if rech == '':
             compte = len(Produit.objects.all())  
        
    else:
        p = Paginator(Produit.objects.all().order_by('-id'), 20)
        page = request.GET.get('page')
        pages =p.get_page(page)
        compte = len(Produit.objects.all())
    ctx = {
        'compte' : compte,
        'produit' : pages,
        'lproduit': 'active',
        'pages':pages
    }
    
    return render(request,"pages/produit.html",ctx)


def fProduit(request):
    
    appart = Appartement.objects.all()
    ctx ={
        "appart":appart
    }
    
    return render(request,"formulaires/produit.html",ctx)


def addProduit(request):
    appart = Appartement.objects.all()
    compte = len(Produit.objects.all())
    if request.method == 'POST':
        msg = None
        msok = None
        nom = request.POST.get("nom",None)
        pu = request.POST.get("pu",0)
        appartement = request.POST.get("appartement",None)
 
        if nom == '':
            msg ="Veuillez remplir le nom"
        elif len(pu) <= 0:
            msg ="Veuillez remplir le pu"
        elif not pu.isnumeric():
            msg ="Prix doit être un numérique"
        elif appartement == '':
            msg ="Veuillez remplir le appartement"
        else:
            apr = Appartement.objects.get(pk=appartement)
            pr = Produit(
                nom = nom.upper(),
                pu = pu,
                appartement=apr
            )
            pr.save()
            msok = "Opération réussie"
            return HttpResponseRedirect('/produit/')
        
    ctx ={
        'msg':msg,
        'msok': msok,
        'compte' : compte,
        'appart':appart
    }
    return render(request,'formulaires/produit.html',ctx)

def modProduit(request,id):
    pr= Produit.objects.get(pk=id)
    appart = Appartement.objects.all()
    
    ctx ={
        'pr': pr,
        'appart':appart
    }
    return render(request,'formulaires/modProduit.html',ctx)

def updateProduit(request,id):
    appart = Appartement.objects.all()
    pr = Produit.objects.get(pk=id)
    print(pr.id)
    if request.method == 'POST':
        msg = None
        msok =None
        
        nom = request.POST.get("nom",None)
        pu = request.POST.get("pu",0)
        appartement = request.POST.get("appartement",None)
     
        if nom == '':
            msg ="Veuillez remplir le nom"
        elif len(pu) <= 0:
            msg ="Veuillez remplir le pu"
        elif not pu.isnumeric():
            msg ="Prix doit être un numérique"
        elif appartement == '':
            msg ="Veuillez remplir le appartement"
        else: 
            apr = Appartement.objects.get(pk=appartement)
            pr.nom = nom.upper()
            pr.appartement = apr
            pr.pu = pu
           
            pr.save()
            msok = nom +" modifié avec succès"
            return HttpResponseRedirect('/produit/')
    ctx ={
        'msg':msg,
        'msok': msok,
        'appart':appart 
    }
    return render(request,'formulaires/modProduit.html',ctx)

def deleteProduit(request,id):
    p = Produit.objects.get(pk=id)
    p.delete()
    return HttpResponseRedirect('/produit/')






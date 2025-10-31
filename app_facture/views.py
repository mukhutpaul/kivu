from django.shortcuts import render

from app_facture.models.appartement import Appartement
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect

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

def produit(request):
    nbrhomme = 0
    nbrFemme = 0

    ctx ={
        'lproduit':'active',
        'nbrhomme':nbrhomme,
        'nbrFemme':nbrFemme,
    }
    
    return render(request,"pages/produit.html",ctx)

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
            #return HttpResponseRedirect('/appartement/')
        else:
            ap = Appartement(
                nom = nom.upper(),
            )
            ap.save()
            msok = "Opération réussie"
            #return HttpResponseRedirect('/appartement/')
        
    ctx ={
        'msg':msg,
        'msok': msok,
        'compte' : compte,
        'appartement' : pages,
        'lapr': 'active',
        'pages':pages
    }
    return render(request,'pages/appartement.html',ctx)


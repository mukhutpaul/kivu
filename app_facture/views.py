from django.shortcuts import render, redirect
from app_facture.models.appartement import Appartement
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from app_facture.models.facture import Facture
from app_facture.models.produit import Produit
from app_facture.models.user import Profile, User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login as auth_login, logout

# Create your views here.
@login_required(login_url="sign_in")
def home(request):
    nbrhomme = 0
    nbrFemme = 0

    ctx ={
        'hm':'active',
        "noms": request.user.noms,
        "username": request.user.username,
        'nbrhomme':nbrhomme,
        "profile": request.user.profile,
        'nbrFemme':nbrFemme,
    }
    
    return render(request,"pages/home.html",ctx)

@login_required(login_url="sign_in")
def facture(request):
    nbrhomme = 0
    nbrFemme = 0

    ctx ={
        'lfact':'active',
        'nbrhomme':nbrhomme,
        'nbrFemme':nbrFemme,
        "noms": request.user.noms,
        "profile": request.user.profile,
    }
    
    return render(request,"pages/facture.html",ctx)


#APPARTEMENT
@login_required(login_url="sign_in")
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
        "noms": request.user.noms,
        "profile": request.user.profile,
        'pages':pages
    }
    
    return render(request,"pages/appartement.html",ctx)

@login_required(login_url="sign_in")
def fAppartement(request):
    nbrhomme = 0
    nbrFemme = 0

    ctx ={
        'lfact':'active',
        'nbrhomme':nbrhomme,
        "noms": request.user.noms,
        "profile": request.user.profile,
        'nbrFemme':nbrFemme,
    }
    
    return render(request,"formulaires/appartement.html",ctx)

@login_required(login_url="sign_in")
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
        "noms": request.user.noms,
        "profile": request.user.profile,
        'lapr': 'active',
        'pages':pages
    }
    return render(request,'formulaires/appartement.html',ctx)

@login_required(login_url="sign_in")
def modAppartement(request,id):
    ap= Appartement.objects.get(pk=id)
    
    ctx ={
        'ap': ap
    }
    return render(request,'formulaires/modAppartement.html',ctx)

@login_required(login_url="sign_in")
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
        'msok': msok ,
        "noms": request.user.noms,
        "profile": request.user.profile,
    }
    return render(request,'formulaires/modAppartement.html',ctx)

@login_required(login_url="sign_in")
def deleteAppartement(request,id):
    p = Appartement.objects.get(pk=id)
    p.delete()
    return HttpResponseRedirect('/appartement/')

#####################################################
#PRODUITS
#####################################################

#PRODUIT
@login_required(login_url="sign_in")
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
        "noms": request.user.noms,
        "profile": request.user.profile,
        'pages':pages
    }
    
    return render(request,"pages/produit.html",ctx)

@login_required(login_url="sign_in")
def fProduit(request):
    
    appart = Appartement.objects.all()
    ctx ={
        "appart":appart,
        "noms": request.user.noms,
        "profile": request.user.profile,
    }
    
    return render(request,"formulaires/produit.html",ctx)

@login_required(login_url="sign_in")
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
        "noms": request.user.noms,
        "profile": request.user.profile,
        'appart':appart
    }
    return render(request,'formulaires/produit.html',ctx)

@login_required(login_url="sign_in")
def modProduit(request,id):
    pr= Produit.objects.get(pk=id)
    appart = Appartement.objects.all()
    
    ctx ={
        'pr': pr,
        'appart':appart,
        "noms": request.user.noms,
        "profile": request.user.profile,
    }
    return render(request,'formulaires/modProduit.html',ctx)

@login_required(login_url="sign_in")
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
        'appart':appart,
        "noms": request.user.noms,
        "profile": request.user.profile, 
    }
    return render(request,'formulaires/modProduit.html',ctx)

@login_required(login_url="sign_in")
def deleteProduit(request,id):
    p = Produit.objects.get(pk=id)
    p.delete()
    return HttpResponseRedirect('/produit/')

###############USERS##############################""
##UTILISATEURS
@login_required(login_url="sign_in")
def users(request):
    if request.method == "POST":
        rech = request.POST['rech']
        p = Paginator(User.objects.filter(username__contains=rech) |
        User.objects.filter(noms__contains=rech) )
        page = request.GET.get('page')
        pages =p.get_page(page)
        compte = len(pages)
        if rech == '':
             compte = len(User.objects.filter(centre=ct))  
        
    else:
        p = Paginator(User.objects.all().order_by('-id'), 20)
        page = request.GET.get('page')
        pages =p.get_page(page)
        compte = len(User.objects.all())
    ctx = {
        'compte' : compte,
        'users' : pages,
        'luser': 'active',
        "noms": request.user.noms,
        "profile": request.user.profile,
        'pages':pages
    }
    return render(request,'user/user.html',ctx)


@login_required(login_url="sign_in")
def fUser(request):
    profiles = Profile.objects.all()
    
    ctx = {
        'pro': profiles
    }
    
    return render(request,'formulaires/FUser.html',ctx)

##ADD USERS
@login_required(login_url="sign_in")
def addUser(request):
    if request.method == 'POST':
        profiles = Profile.objects.all()
        msg = None
        msok =None
        profile = request.POST.get("profile",None)
        centre = request.POST.get("centre",None)
        noms = request.POST.get("noms",None)
        username = request.POST.get("username",None)
        email = request.POST.get("email",None)
        password = request.POST.get("password",None)

        if email =='':
            msg = "Veuillez remplir le mail"
            profiles = Profile.objects.all()
            
        elif profile=='':
            msg="Veuillez choisir le profile"
            profiles = Profile.objects.all()
            
        elif centre =='':
            msg="Veuillez choisir le centre"
            profiles = Profile.objects.all()
        
        elif len(User.objects.filter(username=username))>0:
            msg="Ce nom utilisateur existe déjà"
            profiles = Profile.objects.all()
            
            
        elif len(User.objects.filter(email=email))>0:
            msg="Cette adresse mail existe déjà"
            profiles = Profile.objects.all() 
        
            
        elif noms=='':
            msg="Veuillez remplir les noms"
            profiles = Profile.objects.all()
            
        elif username =='':
            msg="Veuillez remplir le nom utilisateur"
            profiles = Profile.objects.all()
            
        elif password =='':
            msg="Veuillez remplir le mot de passe"
            profiles = Profile.objects.all()
            
        else:
            pro = Profile.objects.get(pk=profile)
           
            u = User(
                noms = noms.upper(),
                profile = pro,
                username = username.upper(),
                email = email,
                is_active = True
            ) 
            u.set_password(password)
            u.save()
            msok = username+ " est enregistré comme utiisateur"
        
    return render(request,'formulaires/FUser.html',{'msg':msg,'msok':msok,'pro':profiles})



@login_required(login_url="sign_in")
def updateUser(request,id):
    user= User.objects.get(pk=id)
    
    if request.method == 'POST':
        profiles = Profile.objects.all()
        msg = None
        msok =None
        profile = request.POST.get("profile",None)
        noms = request.POST.get("noms",None)
        username = request.POST.get("username",None)
        email = request.POST.get("email",None)
        password = request.POST.get("password",None)

        if email =='':
            msg = "Veuillez remplir le mail"
            profiles = Profile.objects.all()
        elif profile=='':
            msg="Veuillez choisir le profile"
            profiles = Profile.objects.all()
        
        # elif len(User.objects.filter(username=username))>0:
        #     msg="Ce nom utilisateur existe déjà"
        #     profiles = Profile.objects.all()
            
        # elif len(User.objects.filter(email=email))>0:
        #     msg="Cette adresse mail existe déjà"
        #     profiles = Profile.objects.all() 
        elif noms=='':
            msg="Veuillez remplir les noms"
            profiles = Profile.objects.all()
        elif username =='':
            msg="Veuillez remplir le nom utilisateur"
            profiles = Profile.objects.all()
        elif password =='':
            msg="Veuillez remplir le mot de passe"
            profiles = Profile.objects.all()
        else:
            pro = Profile.objects.get(pk=profile)
            
            
            user.noms = noms.upper()
            user.profile = pro
            user.username = username.upper()
            user.email = email
            user.is_active = True
            
            #user.set_password(password)
            user.save()
            msok = username+ " a été modifié"
            
            return HttpResponseRedirect('/users/')
        
    return render(request,'formulaires/FUser.html',{'msg':msg,'msok':msok,'pro':profiles})

@login_required(login_url="sign_in")
def deleteUser(request,id):
    user = User.objects.get(pk=id)
    user.delete()
    return HttpResponseRedirect('/users/')

@login_required(login_url="sign_in")
def modifierUser(request,id):
    user= User.objects.get(pk=id)
    profile = Profile.objects.all()
    
    ctx ={
        'user': user,
        'pro': profile
    }
    return render(request,'formulaires/FUser.html',ctx)


# USER AUTHENTIFICATION

def login(request):
    
    return render(request,'user/login.html')

def sign_in(request):
    msg = None
    if request.method == "POST":
        username = request.POST.get("username", None)
        password = request.POST.get("password", None)

        user = User.objects.filter(username=username).first()
        if user:
            auth_user = authenticate(username=user.username, password=password)
            if auth_user:
                auth_login(request, auth_user)
                return redirect("home")
            else:
                msg ="mot de pass incorrecte"
        else:
            msg ="User does not exist"
    
    ctx = {
        "msg":msg
    }

    return render(request,'user/login.html',ctx)

def log_out(request):
    logout(request)
    return redirect("sign_in")

########################################FIN USER ######################################"


######################################### FACTURE #######################
@login_required(login_url="sign_in")
def facture(request):
    facture = Facture.objects.all()
    print("MUKHUT",request.user.profile)
    if request.method == "POST":
        rech = request.POST['rech']
        if request.user.profile.id == 3:
            p = Paginator(Facture.objects.filter(id__contains=rech,user=request.user),12)
            page = request.GET.get('page')
            pages =p.get_page(page)
            compte = len(pages)
        else :
            p = Paginator(Facture.objects.filter(id__contains=rech),12)
            page = request.GET.get('page')
            pages =p.get_page(page)
            compte = len(pages)
            
        if rech == '' and request.user.profile.id == 3:
             compte = len(Facture.objects.filter(user=request.user))
        else:
            compte = len(Facture.objects.all())  
    else:
        if request.user.profile.id == 3:  
            p = Paginator(Facture.objects.filter(user=request.user.id).order_by('-id'),12)
            page = request.GET.get('page')
            pages =p.get_page(page)
            compte = len(pages)
        else:
            p = Paginator(Facture.objects.all().order_by('-id'), 4)
            page = request.GET.get('page')
            pages =p.get_page(page)
            compte = len(Appartement.objects.all())
    ctx = {
        'compte' : compte,
        'facture' : pages,
        'lapr': 'active',
        "noms": request.user.noms,
        "profile": request.user.profile,
        'pages':pages
    }
    
    return render(request,"pages/facture.html",ctx)


def addFacture(request):
    userId = User.objects.get(pk=request.user.id)
    
    f = Facture(
     user = userId
    )
    f.save()
    return HttpResponseRedirect('/facture/')
 

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
        'msok': msok,
        "noms": request.user.noms,
        "profile": request.user.profile, 
    }
    return render(request,'formulaires/modAppartement.html',ctx)

def deleteAppartement(request,id):
    p = Appartement.objects.get(pk=id)
    p.delete()
    return HttpResponseRedirect('/appartement/')




    


















































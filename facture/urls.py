"""
URL configuration for facture project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from app_facture.views import addAppartement, addDetailFacture, addFacture, addProduit, addUser, appartement, deleteAppartement, deleteProduit, deleteUser, deletedetailFacture, detaiFacture, fAppartement, fProduit, fUser, facture, home, log_out, login, modAppartement, modProduit, modifierUser, print_facture, produit, sign_in, updateAppartement, updateProduit, users

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/',home, name="home"),
    
    
    
    #Appartement
    path('appartement/',appartement, name="appartement"),
    path('addAppartement/',addAppartement, name="addAppartement"),
    
    path('fAppartement/',fAppartement, name="fAppartement"),
    path('modAppartement/<int:id>',modAppartement, name="modAppartement"),
    path('updateAppartement/<int:id>',updateAppartement, name="updateAppartement"),
    path('deleteAppartement/<int:id>',deleteAppartement, name="deleteAppartement"),
    
    
    #Produit
    path('produit/',produit, name="produit"),
    path('addProduit/',addProduit, name="addProduit"),
    
    path('fProduit/',fProduit, name="fProduit"),
    path('modProduit/<int:id>',modProduit, name="modProduit"),
    path('updateProduit/<int:id>',updateProduit, name="updateProduit"),
    path('deleteProduit/<int:id>',deleteProduit, name="deleteProduit"),
    
    ##USERS
    path('deleteUser<int:id>/',deleteUser, name="deleteUser"),
    path('users/',users, name="users"),
    path('fUser/',fUser, name="fUser"),
    path('addUser/',addUser, name="addUser"),
    path('modifierUser<int:id>/',modifierUser, name="modifierUser"),
    
        
   #User root
   path('', login, name="login"),
   path('sign_in/', sign_in, name="sign_in"),
   path('log_out/',log_out, name="log_out"),
   
   ##FACTURES
    path('facture/',facture, name="facture"),
    path('addFacture/',addFacture, name="addFacture"),
    
    ##DETAIL FACTURES
    path('detaiFacture/<int:id>',detaiFacture, name="detaiFacture"),
    path('deletedetailFacture/<int:id>',deletedetailFacture, name="deletedetailFacture"),
    path('addDetailFacture/',addDetailFacture, name="addDetailFacture"),
    
    
    ###Imprimer facture
    path('print_facture/<int:id>',print_facture, name="print_facture"),
    
    
    
   
    
    
    
    
    
    
    
    
    
    
    
     
]

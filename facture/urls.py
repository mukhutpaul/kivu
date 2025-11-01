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

from app_facture.views import addAppartement, addProduit, appartement, deleteAppartement, deleteProduit, fAppartement, fProduit, facture, home, modAppartement, modProduit, produit, updateAppartement, updateProduit

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',home, name="home"),
    path('facture/',facture, name="facture"),
    
    
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
    
    
    
    
    
    
    
    
    
    
    
     
]

from django.db import models

from app_facture.models.produit import Produit

# Create your models here.

class Facture(models.Model):
    nom = models.CharField(null=True)
    createdAt = models.DateTimeField(auto_now=True)
    updatedAt = models.DateTimeField()
   
    

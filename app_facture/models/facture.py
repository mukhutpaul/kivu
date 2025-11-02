from django.db import models

from app_facture.models.produit import Produit
from app_facture.models.user import User

# Create your models here.

class Facture(models.Model):
    createdAt = models.DateTimeField(auto_now=True)
    updatedAt = models.DateTimeField(null=True)
    imprimer = models.BooleanField(default=False)
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING,default=1)
    total = models.DecimalField(max_digits=8,decimal_places=2,default=0)
   
    

from django.db import models

from app_facture.models.appartement import Appartement
from app_facture.models.facture import Facture
from app_facture.models.produit import Produit

# Create your models here.


class Detail_facture(models.Model):
    facture = models.ForeignKey(Facture,on_delete=models.DO_NOTHING)
    produit = models.ForeignKey(Produit,on_delete=models.DO_NOTHING)
    quantite = models.IntegerField()
    
    createdAt = models.DateTimeField(auto_now=True)
    updatedAt = models.DateTimeField()
    
    def __str__(self):
        return self.nom +" "+ self.pu
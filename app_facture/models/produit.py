from django.db import models

from app_facture.models.appartement import Appartement

# Create your models here.


class Produit(models.Model):
    nom = models.CharField(max_length=255,null=False)
    pu = models.DecimalField(max_digits=6,decimal_places=2)
    quantite = models.DecimalField(max_digits=6,decimal_places=2,null=True)
    createdAt = models.DateTimeField(auto_now=True)
    updatedAt = models.DateTimeField(null=True)
    
    appartement = models.ForeignKey(Appartement,on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return self.nom
from django.db import models

# Create your models here.

class Appartement(models.Model):
    nom = models.CharField(max_length=255,null=False)
    createdAt = models.DateTimeField(auto_now=True)
    updatedAt = models.DateTimeField(null=True)
    
    def __str__(self):
        return self.nom
    
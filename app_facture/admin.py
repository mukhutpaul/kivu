from django.contrib import admin

from app_facture.models.appartement import Appartement
from app_facture.models.produit import Produit

# Register your models here.

admin.site.register(Appartement)
admin.site.register(Produit)

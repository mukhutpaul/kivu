from django.contrib import admin

from app_facture.models import Detail_facture
from app_facture.models.appartement import Appartement
from app_facture.models.facture import Facture
from app_facture.models.produit import Produit
from app_facture.models.user import Profile

# Register your models here.

admin.site.register(Appartement)
admin.site.register(Produit)
admin.site.register(Facture)
admin.site.register(Detail_facture)
admin.site.register(Profile,list_display=['id','name'])

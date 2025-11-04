from django.core.management import BaseCommand

from app_facture.models.user import Profile



class Command(BaseCommand):
    def handle(self, *args, **options):
        
        liste = ['Manager','Proprietaire','Facturier','Magasinier']
        
        for i in liste:
            p = Profile(
                name = i
            )
            p.save()
from django.db import models

from app_facture.models.facture import Facture
from app_facture.models.produit import Produit


class Detail_facture(models.Model):

    facture = models.ForeignKey(
        Facture,
        on_delete=models.DO_NOTHING
    )

    produit = models.ForeignKey(
        Produit,
        on_delete=models.DO_NOTHING
    )

    # Quantité vendue
    quantite = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    # Prix unitaire TTC au moment de la vente
    pu_ttc = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    # Prix unitaire HT au moment de la vente
    pu_ht = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    # TVA unitaire au moment de la vente
    tva_unitaire = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    # Taux de TVA appliqué
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=16
    )

    createdAt = models.DateTimeField(
        auto_now_add=True
    )

    updatedAt = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.produit.nom} - {self.quantite}"
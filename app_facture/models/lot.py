
from django.db import models

from app_facture.models.produit import Produit


class Lot(models.Model):

    produit = models.ForeignKey(
        Produit,
        on_delete=models.PROTECT,
        related_name="lots"
    )

    numero = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    quantite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    date_peremption = models.DateField()

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.produit.nom} - {self.numero or self.id}"

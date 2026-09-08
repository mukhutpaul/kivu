
from django.db import models

from app_facture.models.lot import Lot
from app_facture.models.produit import Produit
from app_facture.models.user import User


class MouvementStock(models.Model):

    TYPE_ENTREE = "ENTREE"
    TYPE_SORTIE = "SORTIE"
    TYPE_AJUSTEMENT = "AJUSTEMENT"

    TYPE_CHOICES = [
        (TYPE_ENTREE, "Entrée"),
        (TYPE_SORTIE, "Sortie"),
        (TYPE_AJUSTEMENT, "Ajustement"),
    ]

    produit = models.ForeignKey(
        Produit,
        on_delete=models.PROTECT,
        related_name="mouvements_stock"
    )

    lot = models.ForeignKey(
        Lot,
        on_delete=models.PROTECT,
        related_name="mouvements"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="mouvements_stock"
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    quantite = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    stock_avant = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    stock_apres = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    motif = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.type} - "
            f"{self.produit.nom} - "
            f"{self.quantite}"
        )

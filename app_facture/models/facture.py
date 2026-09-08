from django.db import models

from app_facture.models.user import User


class Facture(models.Model):

    createdAt = models.DateTimeField(
        auto_now_add=True
    )

    updatedAt = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True
    )

    imprimer = models.BooleanField(
        default=False
    )

    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        default=1
    )

    # Total hors taxe
    total_ht = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )

    # TVA collectée
    total_tva = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )

    # Total toutes taxes comprises
    total_ttc = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"Facture #{self.id}"
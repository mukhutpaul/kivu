
from decimal import Decimal, ROUND_HALF_UP
import random

from django.db import models

from app_facture.models.appartement import Appartement


class Produit(models.Model):

    # ==========================================================
    # INFORMATIONS PRODUIT
    # ==========================================================

    # Nom du produit
    nom = models.CharField(
        max_length=255,
        null=False
    )

    # Code-barres unique du produit
    code_barre = models.CharField(
        max_length=13,
        unique=True,
        null=False,
        blank=True,
        db_index=True
    )

    # Prix de vente TTC
    pu = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )

    # Quantité disponible en stock
    quantite = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )

    # Seuil minimum de stock
    stock_minimum = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )

    createdAt = models.DateTimeField(
        auto_now_add=True
    )

    updatedAt = models.DateTimeField(
        auto_now=True
    )

    appartement = models.ForeignKey(
        Appartement,
        on_delete=models.DO_NOTHING
    )

    # ==========================================================
    # TVA RDC
    # ==========================================================

    TVA_TAUX = Decimal("16")

    # ==========================================================
    # GÉNÉRATION DU CODE-BARRES
    # ==========================================================

    @staticmethod
    def generer_code_barre():
        """
        Génère un code-barres numérique de 13 chiffres.

        Le code est vérifié avant d'être retourné afin
        d'éviter toute duplication.
        """

        while True:
            code = "".join(
                str(random.randint(0, 9))
                for _ in range(13)
            )

            if not Produit.objects.filter(
                code_barre=code
            ).exists():
                return code

    def save(self, *args, **kwargs):
        """
        Génère automatiquement le code-barres lors
        de la première création du produit.
        """

        if not self.code_barre:
            self.code_barre = self.generer_code_barre()

        super().save(*args, **kwargs)

    # ==========================================================
    # PRIX HT
    # ==========================================================

    @property
    def pu_ht(self):
        """
        Retourne le prix unitaire HT à partir du prix TTC.

        Exemple :
        TTC = 11600
        TVA = 16 %

        HT = 11600 / 1.16
           = 10000
        """

        return (
            self.pu / (
                Decimal("1") +
                self.TVA_TAUX / Decimal("100")
            )
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    # ==========================================================
    # TVA UNITAIRE
    # ==========================================================

    @property
    def tva_unitaire(self):
        """
        Retourne le montant de TVA contenu
        dans le prix TTC.
        """

        return (
            self.pu - self.pu_ht
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    # ==========================================================
    # AFFICHAGE
    # ==========================================================

    def __str__(self):
        return self.nom


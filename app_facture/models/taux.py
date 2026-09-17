from decimal import Decimal
from django.db import models

class TauxJour(models.Model):
    date = models.DateField(
    unique=True,
    db_index=True
)
    taux_usd = models.DecimalField(
    max_digits=20,
    decimal_places=2,
    default=Decimal("0"))
    
    createdAt = models.DateTimeField(
    auto_now_add=True)
    updatedAt = models.DateTimeField(
    auto_now=True
)

class Meta:
    ordering = ["-date"]
    verbose_name = "Taux du jour"
    verbose_name_plural = "Taux du jour"
    def __str__(self):
        return f"{self.date} — 1 USD = {self.taux_usd} FC"
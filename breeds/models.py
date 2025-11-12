from django.db import models

# Create your models here.

SPECIES_CHOICES = [
    ("C", "Canino"),
    ("F", "Felino"),
]


class Breed(models.Model):
    name = models.CharField(max_length=127, verbose_name="Nombre de la raza")
    species = models.CharField(
        max_length=1, choices=SPECIES_CHOICES, verbose_name="Especie"
    )

    class Meta:
        verbose_name = "Raza"
        verbose_name_plural = "Razas"

    def __str__(self):
        return f"{self.name} ({self.get_species_display()})"

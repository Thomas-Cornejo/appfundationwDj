from django.db import models
from breeds.models import Breed

# Create your models here.
SEX_CHOICES = [("M", "Macho"), ("H", "Hembra")]
SIZE_CHOICES = [("G", "Grande"), ("M", "Mediano"), ("P", "Pequeño")]


class Animal(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    birth_date = models.DateField(verbose_name="Fecha de nacimiento aprox.")
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, verbose_name="Sexo")
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, verbose_name="Tamaño")
    color = models.CharField(max_length=20, verbose_name="Color")
    photo = models.ImageField(upload_to="animals/", verbose_name="Foto")
    breed_id = models.ForeignKey(Breed, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name} ({self.breed})"

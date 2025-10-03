from django.db import models
from breeds.models import Breed
from cloudinary.models import CloudinaryField

SEX_CHOICES = [("M", "Macho"), ("H", "Hembra")]
SIZE_CHOICES = [("G", "Grande"), ("M", "Mediano"), ("P", "Pequeño")]
AVAILABILITY_CHOICES = [("A", "Adoption"), ("S","Sponsorship"), ("B","Both")] 
class Animal(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    birth_date = models.DateField(verbose_name="Fecha de nacimiento aprox.")
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, verbose_name="Sexo")
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, verbose_name="Tamaño")
    color = models.CharField(max_length=20, verbose_name="Color")
    imagen = CloudinaryField("image")
    availability = models.CharField(max_length=1, choices=AVAILABILITY_CHOICES, verbose_name="Disponibilidad")
    status = models.BooleanField(default=False, null=False, blank=False)
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, verbose_name="Raza")

    def __str__(self):
        return f"{self.name} ({self.breed})"

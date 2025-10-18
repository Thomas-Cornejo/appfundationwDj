from django.db import models
from breeds.models import Breed
from django.utils import timezone
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
    availability = models.CharField(max_length=1, choices=AVAILABILITY_CHOICES, default="A", verbose_name="Disponibilidad")
    status = models.BooleanField(default=False, null=False, blank=False)
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, verbose_name="Raza")

    def __str__(self):
        return f"{self.name} ({self.breed})"

    def ingreso_history(self):
        return self.history.filter(history_type="I").first()

HISTORY_TYPE_CHOICES = [
    ("V","Vacunacion"),
    ("E","Esterilizacion"),
    ("C","Cirugia"),
    ("I","Ingreso"),
    ('O', 'Otro'),
]
class History(models.Model):
    history_type = models.CharField(max_length=1, choices=HISTORY_TYPE_CHOICES, default="I" ,verbose_name="Tipo de historia")
    description = models.TextField(verbose_name="Descripcion")
    location_found = models.CharField(max_length=255, verbose_name="Dónde se encontró", blank=True, null=True)
    entry_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de historia")
    exit_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de salida")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    animal = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, verbose_name="Animal", related_name="history")

    def __str__(self):
        return f"{self.get_history_type_display()} - {self.animal.name}"


from django.db import models
from django.conf import settings
# Create your models here.

class Shelter(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre del albergue")
    email = models.CharField(max_length=255, verbose_name="Email del alberguer")
    description = models.TextField(blank=True, null=True, verbose_name="Descripcion")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    food_unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=2000, verbose_name="Costo unitario del alimento (COP)")
    hygiene_unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=2000, verbose_name="Costo unitario de la higiene (COP)")
    food_degradation_hours = models.SmallIntegerField(default=8, verbose_name="Horas para degradacion del alimento") 
    food_degradation_percentag = models.SmallIntegerField(default=10, verbose_name="Porcentaje de degradacion del alimento")
    hygiene_degradation_hours = models.SmallIntegerField(default=24, verbose_name="Horas para degradacion de la higiene")
    hygiene_degradation_percentage  = models.SmallIntegerField(default=10, verbose_name="Porcentaje de degradacion de la higiene")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Albergue"
        verbose_name_plural = "Albergues"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    

from django.contrib import admin
from .models import Breed


class BreedAnimal(admin.ModelAdmin):
    model = Breed


admin.site.register(Breed, BreedAnimal)

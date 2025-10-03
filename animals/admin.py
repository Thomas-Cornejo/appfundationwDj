from django.utils.html import format_html
from django.contrib import admin
from .models import Animal

class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'breed', 'sex', 'size', 'color', 'preview_image')
    list_filter = ("breed__species", "sex", "size")
    
    def get_species(self, obj):
        return obj.breed.get_species_display()
    get_species.short_description = "Especie"

    def preview_image(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="120" height="120" />', obj.imagen.url)
        return "No image"

    preview_image.short_description = "Vista previa"

admin.site.register(Animal, AnimalAdmin)

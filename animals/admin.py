from django.utils.html import format_html
from django.contrib import admin
from .models import Animal, History


class HistoryInline(admin.StackedInline):
    model = History
    extra = 1
    fieldsets = (
        (None, {"fields": ("history_type", "description", "location_found", "entry_date")}),
    )
    readonly_fields = ("entry_date",)
    show_change_link = True

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("name", "breed", "sex", "size", "color", "preview_image")
    list_filter = ("breed__species", "sex", "size")
    inlines = [HistoryInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "birth_date",
                    "breed",
                    "sex",
                    "size",
                    "color",
                    "availability",
                    "imagen",
                )
            },
        ),
    )

    def preview_image(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" width="120" height="120" style="border-radius:10px;" />',
                obj.imagen.url,
            )
        return "Sin imagen"

    preview_image.short_description = "Vista previa"

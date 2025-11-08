from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from shelters.models import Shelter

from .models import Animal, History


class HistoryInline(admin.StackedInline):
    model = History
    extra = 1
    max_num = 1
    fieldsets = (
        (
            "Historia de Ingreso",
            {
                "fields": (
                    "history_type",
                    "description",
                    "location_found",
                    "entry_date",
                ),
                "description": "📝 Registra cómo y dónde llegó el animal. Para eventos médicos, usa el admin de 'Historias' después de guardar.",
            },
        ),
    )

    readonly_fields = ("entry_date",)
    show_change_link = True

    def get_formset(self, request, obj=None, **kwargs):
        """Configurar valores por defecto"""
        formset = super().get_formset(request, obj, **kwargs)

        if not obj:
            formset.form.base_fields["history_type"].initial = "I"

        return formset

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar historial"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        return False


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "breed",
        "age",
        "sex",
        "size",
        "color",
        "shelter",
        "availability",
        "is_active",
        "preview_image",
    ]

    list_filter = [
        "shelter",
        "breed__species",
        "availability",
        "sex",
        "size",
        "is_active",
    ]

    search_fields = ["name", "shelter__name", "breed__name"]

    readonly_fields = ["created_at", "updated_at", "age"]

    inlines = [HistoryInline]

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "name",
                    "birth_date",
                    "age",
                    "breed",
                    "sex",
                    "size",
                    "color",
                )
            },
        ),
        (
            "Albergue y Disponibilidad",
            {
                "fields": (
                    "shelter",
                    "availability",
                    "is_active",
                )
            },
        ),
        ("Imagen", {"fields": ("imagen",)}),
        (
            "Metadatos",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def preview_image(self, obj):
        """Muestra preview de la imagen del animal"""
        if obj.imagen:
            return format_html(
                '<img src="{}" width="120" height="120" style="border-radius:10px; object-fit: cover;" />',
                obj.imagen.url,
            )
        return format_html(
            '<div style="width:120px; height:120px; background:#e0e0e0; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#666;">Sin imagen</div>'
        )

    preview_image.short_description = "Vista previa"

    def get_queryset(self, request):
        """Filtrar animales según rol"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return qs

        if (
            hasattr(request.user, "is_shelter_admin")
            and request.user.is_shelter_admin()
        ):
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(shelter=request.user.shelter)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restringir opciones de ForeignKey según permisos"""
        if db_field.name == "shelter":
            if request.user.is_superuser:
                pass
            elif (
                hasattr(request.user, "is_superadmin") and request.user.is_superadmin()
            ):
                pass
            elif (
                hasattr(request.user, "is_shelter_admin")
                and request.user.is_shelter_admin()
            ):
                if hasattr(request.user, "shelter") and request.user.shelter:
                    kwargs["queryset"] = Shelter.objects.filter(
                        id=request.user.shelter.id
                    )
                    if not kwargs.get("initial"):
                        kwargs["initial"] = request.user.shelter.id

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar animales"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        return False

    def has_add_permission(self, request):
        """Super Admin y Shelter Admin pueden agregar animales"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        if (
            hasattr(request.user, "is_shelter_admin")
            and request.user.is_shelter_admin()
        ):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Super Admin y Shelter Admin pueden editar animales"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True

        if (
            hasattr(request.user, "is_shelter_admin")
            and request.user.is_shelter_admin()
        ):
            if obj is None:
                return True
            if hasattr(request.user, "shelter"):
                return obj.shelter == request.user.shelter

        return False

    actions = [
        "mark_as_available_for_adoption",
        "mark_as_available_for_sponsorship",
        "mark_as_available_for_both",
    ]

    def mark_as_available_for_adoption(self, request, queryset):
        """Marcar como disponible solo para adopción"""
        updated = queryset.update(availability="A")
        self.message_user(
            request, f"{updated} animal(es) marcado(s) como disponible para adopción."
        )

    mark_as_available_for_adoption.short_description = (
        "Marcar como disponible para adopción"
    )

    def mark_as_available_for_sponsorship(self, request, queryset):
        """Marcar como disponible solo para apadrinamiento"""
        updated = queryset.update(availability="S")
        self.message_user(
            request,
            f"{updated} animal(es) marcado(s) como disponible para apadrinamiento.",
        )

    mark_as_available_for_sponsorship.short_description = (
        "Marcar como disponible para apadrinamiento"
    )

    def mark_as_available_for_both(self, request, queryset):
        """Marcar como disponible para ambos"""
        updated = queryset.update(availability="B")
        self.message_user(
            request, f"{updated} animal(es) marcado(s) como disponible para ambos."
        )

    mark_as_available_for_both.short_description = "Marcar como disponible para ambos"

    def save_related(self, request, form, formsets, change):
        """
        Validar que al crear un animal, se incluya al menos 1 historia de ingreso.
        """
        super().save_related(request, form, formsets, change)
        if not change:
            animal = form.instance
            if not animal.history.exists():
                from django.contrib import messages

                messages.warning(
                    request,
                    f"⚠️ Advertencia: {animal.name} fue creado sin historia de ingreso. "
                    "Por favor, agrega una historia en la pestaña 'Historias'.",
                )


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    """Admin para gestionar el historial médico directamente"""

    list_display = [
        "id",
        "entry_date",
        "animal",
        "shelter_display",
        "history_type_badge",
        "status_badge",
        "urgent_icon",
        "progress_bar",
        "remaining_display",
        "description_preview",
    ]

    list_filter = [
        "history_type",
        "status",
        "is_urgent",
        "entry_date",
        "animal__shelter",
    ]

    search_fields = ["animal__name", "description", "animal__shelter__name"]

    readonly_fields = [
        "entry_date",
        "created_at",
        "updated_at",
        "contributed_coins",
        "progress_percentage",
        "remaining_coins",
        "is_fully_funded",
        "is_health_event",
    ]

    fieldsets = (
        (
            "Información del Evento",
            {
                "fields": (
                    "animal",
                    "history_type",
                    "description",
                    ("entry_date", "exit_date"),
                )
            },
        ),
        (
            "Evento de Salud",
            {
                "fields": (
                    "status",
                    "is_urgent",
                    "health_impact",
                ),
                "description": "Solo aplica para eventos médicos (Vacunación, Cirugía, Tratamiento, Urgencia)",
            },
        ),
        (
            "Financiamiento",
            {
                "fields": (
                    ("cost_coins", "contributed_coins"),
                    "progress_percentage",
                    "remaining_coins",
                    "is_fully_funded",
                    "is_health_event",
                ),
                "classes": ("collapse",),
                "description": "Sistema de contribuciones para tratamientos médicos",
            },
        ),
        (
            "Metadatos",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["mark_as_completed", "apply_health_impact_action"]

    def get_fieldsets(self, request, obj=None):
        """
        Mostrar 'location_found' solo si el tipo de historia es 'Ingreso'.
        """
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.history_type == "I":
            fieldsets = list(fieldsets)
            info_evento = list(fieldsets[0][1]["fields"])

            if "location_found" not in info_evento:
                info_evento.insert(2, "location_found")

            fieldsets[0] = (fieldsets[0][0], {"fields": tuple(info_evento)})
            return tuple(fieldsets)

        if obj is None:
            fieldsets = list(fieldsets)
            info_evento = list(fieldsets[0][1]["fields"])

            if "location_found" not in info_evento:
                info_evento.insert(2, "location_found")

            fieldsets[0] = (fieldsets[0][0], {"fields": tuple(info_evento)})
            return tuple(fieldsets)

        return fieldsets

    def shelter_display(self, obj):
        """Muestra el albergue del animal"""
        if obj.animal and obj.animal.shelter:
            return obj.animal.shelter.name
        return "-"

    shelter_display.short_description = "Albergue"

    def history_type_badge(self, obj):
        """Badge colorizado según el tipo de evento"""
        colors = {
            "I": "#6b7280",
            "V": "#10b981",
            "C": "#3b82f6",
            "E": "#8b5cf6",
            "T": "#f59e0b",
            "U": "#ef4444",
            "O": "#6b7280",
        }
        color = colors.get(obj.history_type, "#6b7280")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color,
            obj.get_history_type_display(),
        )

    history_type_badge.short_description = "Tipo"

    def status_badge(self, obj):
        """Badge de estado solo para eventos de salud"""
        if not obj.is_health_event:
            return "-"

        colors = {
            "P": "#ef4444",
            "T": "#f59e0b",
            "C": "#10b981",
        }
        color = colors.get(obj.status, "#6b7280")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Estado"

    def urgent_icon(self, obj):
        """Icono de urgencia"""
        if obj.is_urgent:
            return format_html(
                '<span style="font-size: 18px;" title="¡Urgente!">🚨</span>'
            )
        return "-"

    urgent_icon.short_description = "🚨"

    def progress_bar(self, obj):
        """Barra de progreso visual para eventos con costo"""
        if not obj.is_health_event:
            return "-"

        percentage = obj.progress_percentage
        color = "#10b981" if percentage == 100 else "#3b82f6"

        return format_html(
            '<div style="width: 100px; background-color: #e5e7eb; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; '
            'padding: 2px 0; font-size: 10px; font-weight: bold;">'
            "{}%%"
            "</div>"
            "</div>",
            percentage,
            color,
            percentage,
        )

    progress_bar.short_description = "Progreso"

    def remaining_display(self, obj):
        """Muestra cuánto falta para completar"""
        if not obj.is_health_event:
            return "-"

        remaining = obj.remaining_coins
        if remaining == 0:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Completo</span>'
            )

        return format_html(
            '<span style="color: #ef4444; font-weight: bold;">🪙 {}</span>', remaining
        )

    remaining_display.short_description = "Falta"

    def description_preview(self, obj):
        """Preview corto de la descripción"""
        if obj.description and len(obj.description) > 60:
            return obj.description[:60] + "..."
        return obj.description or "-"

    description_preview.short_description = "Descripción"

    def mark_as_completed(self, request, queryset):
        """Marca eventos como completados manualmente"""
        count = 0
        for event in queryset.filter(status__in=["P", "T"]):
            event.resolve_event()
            count += 1

        self.message_user(
            request,
            f"✅ {count} evento(s) marcado(s) como completado(s) y salud restaurada.",
        )

    mark_as_completed.short_description = "✅ Marcar como completados"

    def apply_health_impact_action(self, request, queryset):
        """Aplica el impacto de salud para eventos pendientes"""
        count = 0
        errors = 0

        for event in queryset.filter(status="P", health_impact__gt=0):
            if event.apply_health_impact():
                count += 1
            else:
                errors += 1

        if count > 0:
            self.message_user(
                request, f"⚠️ Impacto aplicado a {count} animal(es). Salud reducida."
            )

        if errors > 0:
            self.message_user(
                request,
                f"⚠️ {errors} evento(s) no pudieron aplicarse (animal sin CareIndicator activo)",
                level="warning",
            )

    apply_health_impact_action.short_description = "⚠️ Aplicar impacto en salud"

    def get_queryset(self, request):
        """Filtrar historial según albergue del animal"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return qs

        if (
            hasattr(request.user, "is_shelter_admin")
            and request.user.is_shelter_admin()
        ):
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(animal__shelter=request.user.shelter)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restringir animales visibles al crear historial"""
        if db_field.name == "animal":
            if not request.user.is_superuser:
                if not (
                    hasattr(request.user, "is_superadmin")
                    and request.user.is_superadmin()
                ):
                    if (
                        hasattr(request.user, "is_shelter_admin")
                        and request.user.is_shelter_admin()
                    ):
                        if hasattr(request.user, "shelter") and request.user.shelter:
                            kwargs["queryset"] = Animal.objects.filter(
                                shelter=request.user.shelter
                            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar historial"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        return False

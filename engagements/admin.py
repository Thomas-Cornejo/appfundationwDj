from django.conf import settings
from django.contrib import admin
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.html import format_html

from .models import AnimalEngagement, Visit


@admin.register(AnimalEngagement)
class AnimalEngagementAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "animal",
        "shelter_display",
        "engagement_type_badge",
        "status_badge",
        "created_at",
        "download_pdf_link",
    ]
    list_filter = ["engagements_type", "status", "created_at", "animal__shelter"]
    search_fields = [
        "user__username",
        "user__email",
        "animal__name",
        "animal__shelter__name",
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["created_at", "updated_at", "form_data_display", "download_pdf_button"]
        return ["created_at", "updated_at"]

    fieldsets = (
        (
            "Información básica",
            {"fields": ("user", "animal", "engagements_type", "status")},
        ),
        (
            "Detalles de la solicitud",
            {
                "fields": (
                    "form_data_display",
                    "download_pdf_button",
                    "admin_notes",
                )
            },
        ),
        ("Fechas", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (
            "Información básica",
            {"fields": ("user", "animal", "engagements_type", "status")},
        ),
        ("Notas del administrador", {"fields": ("admin_notes",)}),
    )

    def get_fieldsets(self, request, obj=None):
        """Usar fieldsets diferentes para crear vs editar"""
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    actions = ["approve_engagements", "reject_engagements"]

    def shelter_display(self, obj):
        """Show the animal's shelter"""
        return obj.animal.shelter.name if obj.animal.shelter else "-"

    shelter_display.short_description = "Albergue"

    def get_queryset(self, request):
        """Filter engagements based on user role"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(animal__shelter=request.user.shelter)
            return qs.none()

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limitar animales disponibles según el rol"""
        if db_field.name == "animal":
            if request.user.is_superuser:
                pass
            elif request.user.groups.filter(name="Super Admin").exists():
                pass
            elif request.user.groups.filter(name="Shelter Admin").exists():
                if hasattr(request.user, "shelter") and request.user.shelter:
                    from animals.models import Animal

                    kwargs["queryset"] = Animal.objects.filter(shelter=request.user.shelter)
                else:
                    from animals.models import Animal

                    kwargs["queryset"] = Animal.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        """Super Admin y Shelter Admin pueden crear engagements manualmente"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name__in=["Super Admin", "Shelter Admin"]).exists():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete engagements"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """
        Super Admin and Shelter Admin can change the status.
        Shelter Admin can only change engagements for their shelter.
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True

        if request.user.groups.filter(name="Shelter Admin").exists():
            if obj is None:
                return True
            if hasattr(request.user, "shelter") and request.user.shelter:
                return obj.animal.shelter == request.user.shelter
            return False

        return False

    def form_data_display(self, obj):
        """Displays form data in a readable format"""
        if obj and obj.form_data:
            html = "<table style='width:100%; border-collapse: collapse;'>"
            for key, value in obj.form_data.items():
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                html += f"<tr style='border-bottom: 1px solid #ddd;'>"
                html += f"<td style='padding: 8px; font-weight: bold;'>{key.replace('_', ' ').title()}:</td>"
                html += f"<td style='padding: 8px;'>{value if value else 'N/A'}</td>"
                html += "</tr>"
            html += "</table>"
            return format_html(html)
        return "No hay datos de formulario"

    form_data_display.short_description = "Datos del formulario"

    def engagement_type_badge(self, obj):
        """Badge color-coded according to the type of engagement"""
        colors = {"A": "#10b981", "S": "#9333EA", "D": "#f59e0b"}
        color = colors.get(obj.engagements_type, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{}</span>',
            color,
            obj.get_engagements_type_display(),
        )

    engagement_type_badge.short_description = "Tipo"

    def status_badge(self, obj):
        """Badge color according to state"""
        colors = {"P": "#f59e0b", "A": "#10b981", "R": "#ef4444"}
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Estado"

    def download_pdf_link(self, obj):
        """Enlace para descargar PDF en la lista de registros"""
        if obj.form_data:
            download_url = reverse("download_engagement_pdf", args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" '
                'style="background-color:#2563eb; color:white; padding:6px 10px; '
                "border-radius:6px; text-decoration:none; box-shadow:0 2px 4px rgba(0,0,0,0.1); "
                'display:inline-block;">'
                "📄 PDF</a>",
                download_url,
            )
        return format_html('<span style="color:#9ca3af; font-size:12px;">Sin datos</span>')

    download_pdf_link.short_description = "Descargar"

    def download_pdf_button(self, obj):
        """Botón grande para descargar PDF en la vista de detalle"""
        if obj and obj.pk and obj.form_data:
            download_url = reverse("download_engagement_pdf", args=[obj.id])
            tipo = "Adopción" if obj.engagements_type == "A" else "Apadrinamiento"
            return format_html(
                '<a href="{}" target="_blank" '
                'style="display:inline-block; background-color:#2563eb; color:white; '
                "padding:12px 24px; border-radius:8px; text-decoration:none; "
                "font-weight:bold; box-shadow:0 4px 6px rgba(0,0,0,0.1); "
                'transition:all 0.3s;">'
                "📄 Descargar PDF de {}</a>",
                download_url,
                tipo,
            )
        return format_html(
            '<span style="color:#9ca3af;">Guarda el registro primero para generar el PDF</span>'
        )

    download_pdf_button.short_description = "Documento PDF"

    def approve_engagements(self, request, queryset):
        """Mass action to approve applications"""
        updated = queryset.filter(status__in=["P", "R"]).update(status="A")
        self.message_user(request, f"{updated} solicitud(es) aprobada(s) exitosamente.")

    approve_engagements.short_description = "Aprobar solicitudes seleccionadas"

    def reject_engagements(self, request, queryset):
        """Mass action to reject applications"""
        updated = queryset.filter(status__in=["P", "A"]).update(status="R")
        self.message_user(request, f"{updated} solicitud(es) rechazada(s).")

    reject_engagements.short_description = "Rechazar solicitudes seleccionadas"

    def save_model(self, request, obj, form, change):
        """
        Al guardar, los signals se encargan de:
        1. Enviar correos cuando cambia el estado
        2. Crear CareIndicator si es apadrinamiento aprobado
        """
        super().save_model(request, obj, form, change)

        if obj.engagements_type == "S" and obj.status == "A":
            self.message_user(
                request,
                f"Apadrinamiento aprobado. El CareIndicator se creará automáticamente.",
                level="SUCCESS",
            )


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "animal_display",
        "user_display",
        "visit_date",
        "status_badge",
        "evaluation_badge",
        "created_at",
    ]
    list_filter = ["completed", "visit_date", "evaluation", "animal_engagement__animal__shelter"]
    search_fields = [
        "animal_engagement__user__username",
        "animal_engagement__user__email",
        "animal_engagement__animal__name",
        "notes",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Información de la Visita",
            {
                "fields": (
                    "animal_engagement",
                    "visit_date",
                    "completed",
                )
            },
        ),
        (
            "Evaluación y Notas",
            {
                "fields": ("evaluation", "notes"),
                "description": "La evaluación se completa después de realizar la visita.",
            },
        ),
        ("Fechas", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    actions = ["mark_as_completed"]

    def get_queryset(self, request):
        """Filtrar visitas según el rol del usuario"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(animal_engagement__animal__shelter=request.user.shelter)
            return qs.none()

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limitar engagements disponibles según el rol"""
        if db_field.name == "animal_engagement":
            if request.user.is_superuser:
                pass
            elif request.user.groups.filter(name="Super Admin").exists():
                pass

            elif request.user.groups.filter(name="Shelter Admin").exists():
                if hasattr(request.user, "shelter") and request.user.shelter:
                    kwargs["queryset"] = AnimalEngagement.objects.filter(
                        animal__shelter=request.user.shelter
                    )
                else:
                    kwargs["queryset"] = AnimalEngagement.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        """Super Admin y Shelter Admins pueden crear visitas"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name__in=["Super Admin", "Shelter Admin"]).exists():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar visitas"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Super Admin y Shelter Admin pueden modificar visitas"""

        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True

        if request.user.groups.filter(name="Shelter Admin").exists():
            if obj is None:
                return True
            if hasattr(request.user, "shelter") and request.user.shelter:
                return obj.animal_engagement.animal.shelter == request.user.shelter
            return False

        return False

    def animal_display(self, obj):
        """Muestra el nombre del animal"""
        return obj.animal_engagement.animal.name

    animal_display.short_description = "Animal"

    def user_display(self, obj):
        """Muestra el usuario adoptante"""
        return obj.animal_engagement.user.username

    user_display.short_description = "Usuario Adoptante"

    def status_badge(self, obj):
        """Badge indicando si la visita está completada o pendiente"""
        if obj.completed:
            color = "#10b981"
            text = "Realizada"
        else:
            from django.utils import timezone

            if obj.visit_date > timezone.now():
                color = "#f59e0b"
                text = "Programada"
            else:
                color = "#ef4444"
                text = "Vencida"

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 12px;">{}</span>',
            color,
            text,
        )

    status_badge.short_description = "Estado"

    def evaluation_badge(self, obj):
        """Badge con la evaluación de la visita"""
        if obj.evaluation is None:
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 10px; '
                'border-radius: 10px; font-size: 12px;">Sin evaluar</span>'
            )

        colors = {
            1: "#ef4444",
            2: "#f97316",
            3: "#f59e0b",
            4: "#84cc16",
            5: "#10b981",
        }

        stars = "⭐" * obj.evaluation
        color = colors.get(obj.evaluation, "#6b7280")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 12px;">{} {}</span>',
            color,
            stars,
            obj.get_evaluation_display(),
        )

    evaluation_badge.short_description = "Evaluación"

    def mark_as_completed(self, request, queryset):
        """Acción para marcar visitas como completadas"""
        updated = queryset.update(completed=True)
        self.message_user(request, f"{updated} visita(s) marcada(s) como completada(s).")

    mark_as_completed.short_description = "Marcar como completadas"

    def save_model(self, request, obj, form, change):
        """Enviar email al usuario cuando se programa una nueva visita"""
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new:
            self.send_visit_notification_email(obj)
            self.message_user(
                request,
                f"Visita programada. Se ha enviado un correo a {obj.animal_engagement.user.email}",
                level="SUCCESS",
            )

    def send_visit_notification_email(self, visit):
        """Enviar correo al usuario adoptante sobre la visita programada"""
        subject = f"Visita Programada - {visit.animal_engagement.animal.name}"

        message = f"""
Hola {visit.animal_engagement.user.username},

Te informamos que se ha programado una visita de seguimiento para {visit.animal_engagement.animal.name}.

Detalles de la visita:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Animal: {visit.animal_engagement.animal.name}
- Fecha y hora: {visit.visit_date.strftime('%d/%m/%Y a las %H:%M')}
- Raza: {visit.animal_engagement.animal.breed.name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Esta visita tiene como objetivo verificar que {visit.animal_engagement.animal.name} se encuentre en
óptimas condiciones y evaluar su adaptación a su nuevo hogar.

Por favor, asegúrate de estar disponible en la fecha y hora indicadas.

Puedes ver los detalles de esta y otras visitas en tu perfil, sección "Mis Adopciones".

¡Gracias por cuidar de {visit.animal_engagement.animal.name}! 🐾

Saludos cordiales,
El equipo de la Fundación
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [visit.animal_engagement.user.email],
                fail_silently=False,
            )
            print(f"Email de visita enviado exitosamente a {visit.animal_engagement.user.email}")
        except Exception as e:
            print(f"Error enviando email de visita: {e}")

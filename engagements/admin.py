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
        "view_pdf",
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
            return ["created_at", "updated_at", "pdf_file", "form_data_display"]
        return ["created_at", "updated_at"]

    fieldsets = (
        (
            "Información básica",
            {"fields": ("user", "animal", "engagements_type", "status")},
        ),
        (
            "Detalles de la solicitud",
            {"fields": ("form_data_display", "pdf_file", "admin_notes")},
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
        return obj.animal.shelter.name

    shelter_display.short_description = "Albergue"

    def get_queryset(self, request):
        """Filter engagements based on user role"""
        qs = super().get_queryset(request)

        if request.user.is_superuser or request.user.is_superadmin():
            return qs

        if request.user.is_shelter_admin() and request.user.shelter:
            return qs.filter(animal__shelter=request.user.shelter)

        return qs.none()

    def has_add_permission(self, request):
        """Superadmins y superusers pueden crear engagements manualmente (para pruebas)"""
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete engagements"""
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """
        Super Admin and Shelter Admin can change the status.
        Shelter Admin can only change engagements for their shelter.
        """
        if request.user.is_superuser or request.user.is_superadmin():
            return True

        if request.user.is_shelter_admin():
            if obj is None:
                return True
            return obj.animal.shelter == request.user.shelter

        return False

    def form_data_display(self, obj):
        """Displays form data in a readable format"""
        if obj and obj.form_data:
            html = "<table style='width:100%; border-collapse: collapse;'>"
            for key, value in obj.form_data.items():
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

    def view_pdf(self, obj):
        """Stylish link to view/download the PDF"""
        if obj.pdf_file:
            download_url = reverse("download_pdf", args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" '
                'style="background-color:#2563eb; color:white; padding:6px 10px; '
                'border-radius:6px; text-decoration:none; box-shadow:0 2px 4px rgba(0,0,0,0.1);">'
                "📄 Ver PDF</a>",
                download_url,
            )
        return "-"

    view_pdf.short_description = "PDF"

    def approve_engagements(self, request, queryset):
        """Mass action to approve applications"""
        for engagement in queryset:
            if engagement.status != "A":
                engagement.status = "A"
                engagement.save()
                self.send_status_email(engagement, approved=True)

        self.message_user(request, f"{queryset.count()} solicitud(es) aprobada(s) exitosamente.")

    approve_engagements.short_description = "Aprobar solicitudes seleccionadas"

    def reject_engagements(self, request, queryset):
        """Mass action to reject applications"""
        for engagement in queryset:
            if engagement.status != "R":
                engagement.status = "R"
                engagement.save()
                self.send_status_email(engagement, approved=False)

        self.message_user(request, f"{queryset.count()} solicitud(es) rechazada(s).")

    reject_engagements.short_description = "Rechazar solicitudes seleccionadas"

    def send_status_email(self, engagement, approved):
        """Send an email to the user informing them of the status of their request"""

        engagement_name = engagement.get_engagements_type_display()

        if approved:
            subject = f"¡Tu solicitud de {engagement_name.lower()} ha sido aprobada!"

            if engagement.engagements_type == "A":
                message = f"""
Hola {engagement.user.username},

¡Excelentes noticias! 🎉

Tu solicitud de adopción para {engagement.animal.name} ha sido APROBADA.

Detalles de tu solicitud:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Animal: {engagement.animal.name}
- Raza: {engagement.animal.breed.name}
- Edad: {engagement.animal.age} años
- Fecha de solicitud: {engagement.created_at.strftime('%d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Próximos pasos:
1. Nuestro equipo se pondrá en contacto contigo en las próximas 48 horas
2. Coordinaremos una visita para conocer a {engagement.animal.name}
3. Completaremos el proceso de adopción

¡Gracias por darle una segunda oportunidad a {engagement.animal.name}! 🐾

Saludos cordiales,
El equipo de la Fundación
                """
            else:
                message = f"""
Hola {engagement.user.username},

¡Excelentes noticias!

Tu solicitud de apadrinamiento para {engagement.animal.name} ha sido APROBADA.

Detalles de tu apadrinamiento:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Animal: {engagement.animal.name}
- Raza: {engagement.animal.breed.name}
- Fecha de solicitud: {engagement.created_at.strftime('%d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¿Qué sigue?
1. Recibirás instrucciones de acceso al sistema de gamificación
2. Podrás interactuar con {engagement.animal.name} virtualmente
3. Recibirás actualizaciones sobre su estado y progreso

¡Gracias por tu generosidad y compromiso con {engagement.animal.name}! 🐾

Saludos cordiales,
El equipo de la Fundación
                """
        else:
            subject = f"Actualización sobre tu solicitud de {engagement_name.lower()}"

            message = f"""
Hola {engagement.user.username},

Gracias por tu interés en {engagement_name.lower()} a {engagement.animal.name}.

Lamentamos informarte que en este momento tu solicitud no ha sido aprobada.

Detalles de tu solicitud:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Animal: {engagement.animal.name}
- Raza: {engagement.animal.breed.name}
- Fecha de solicitud: {engagement.created_at.strftime('%d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Esto puede deberse a diversos factores relacionados con las necesidades específicas del animal.

Te invitamos a:
- Explorar otros animales disponibles en nuestra fundación
- Contactarnos para más información sobre el proceso

Agradecemos tu interés en ayudar a nuestros animales. 🐾

Saludos cordiales,
El equipo de la Fundación
            """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [engagement.user.email],
                fail_silently=False,
            )
            print(f"Email successfully sent to {engagement.user.email}")
        except Exception as e:
            print(f"Error sending email: {e}")

    def save_model(self, request, obj, form, change):
        """Al guardar, si es un apadrinamiento aprobado, el signal creará automáticamente el CareIndicator"""
        super().save_model(request, obj, form, change)

        if not change and obj.engagements_type == "S" and obj.status == "A":
            self.message_user(
                request,
                f"✅ Apadrinamiento creado. El CareIndicator se creará automáticamente por el signal.",
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

        if request.user.is_superuser or request.user.is_superadmin():
            return qs

        if request.user.is_shelter_admin() and request.user.shelter:
            return qs.filter(animal_engagement__animal__shelter=request.user.shelter)

        return qs.none()

    def has_add_permission(self, request):
        """Superadmins y Shelter Admins pueden crear visitas"""
        if (
            request.user.is_superuser
            or request.user.is_superadmin()
            or request.user.is_shelter_admin()
        ):
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar visitas"""
        if request.user.is_superuser or request.user.is_superadmin():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Super Admin y Shelter Admin pueden modificar visitas"""
        if request.user.is_superuser or request.user.is_superadmin():
            return True

        if request.user.is_shelter_admin():
            if obj is None:
                return True
            return obj.animal_engagement.animal.shelter == request.user.shelter

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
            1: "#ef4444",  # Rojo - Muy Mala
            2: "#f97316",  # Naranja - Mala
            3: "#f59e0b",  # Amarillo - Regular
            4: "#84cc16",  # Lima - Buena
            5: "#10b981",  # Verde - Excelente
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
                f"✅ Visita programada. Se ha enviado un correo a {obj.user.email}",
                level="SUCCESS",
            )

    def send_visit_notification_email(self, visit):
        """Enviar correo al usuario adoptante sobre la visita programada"""
        subject = f"Visita Programada - {visit.animal.name}"

        message = f"""
Hola {visit.user.username},

Te informamos que se ha programado una visita de seguimiento para {visit.animal.name}.

Detalles de la visita:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Animal: {visit.animal.name}
- Fecha y hora: {visit.visit_date.strftime('%d/%m/%Y a las %H:%M')}
- Raza: {visit.animal.breed.name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Esta visita tiene como objetivo verificar que {visit.animal.name} se encuentre en
óptimas condiciones y evaluar su adaptación a su nuevo hogar.

Por favor, asegúrate de estar disponible en la fecha y hora indicadas.

Puedes ver los detalles de esta y otras visitas en tu perfil, sección "Mis Adopciones".

¡Gracias por cuidar de {visit.animal.name}! 🐾

Saludos cordiales,
El equipo de la Fundación
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [visit.user.email],
                fail_silently=False,
            )
            print(f"Email de visita enviado exitosamente a {visit.user.email}")
        except Exception as e:
            print(f"Error enviando email de visita: {e}")

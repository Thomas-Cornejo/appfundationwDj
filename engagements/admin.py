from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from .models import AnimalEngagement

@admin.register(AnimalEngagement)
class AnimalEngagementAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'animal', 'engagement_type_badge', 'status_badge', 'created_at', 'view_pdf']
    list_filter = ['engagements_type', 'status', 'created_at']
    search_fields = ['user__username', 'user__email', 'animal__name']
    readonly_fields = ['created_at', 'updated_at', 'pdf_file', 'form_data_display']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('user', 'animal', 'engagements_type', 'status')
        }),
        ('Detalles de la solicitud', {
            'fields': ('form_data_display', 'pdf_file', 'admin_notes')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_engagements', 'reject_engagements']

    def form_data_display(self, obj):
        """Muestra los datos del formulario de forma legible"""
        if obj.form_data:
            html = "<table style='width:100%; border-collapse: collapse;'>"
            for key, value in obj.form_data.items():
                html += f"<tr style='border-bottom: 1px solid #ddd;'>"
                html += f"<td style='padding: 8px; font-weight: bold;'>{key.replace('_', ' ').title()}:</td>"
                html += f"<td style='padding: 8px;'>{value if value else 'N/A'}</td>"
                html += "</tr>"
            html += "</table>"
            return format_html(html)
        return "No hay datos"
    form_data_display.short_description = 'Datos del formulario'

    def engagement_type_badge(self, obj):
        colors = {'A': '#10b981', 'S': '#3b82f6', 'D': '#f59e0b'}
        color = colors.get(obj.engagements_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_engagements_type_display()
        )
    engagement_type_badge.short_description = 'Tipo'

    def status_badge(self, obj):
        colors = {'P': '#f59e0b', 'A': '#10b981', 'R': '#ef4444'}
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def view_pdf(self, obj):
        if obj.pdf_file:
            download_url = reverse('download_pdf', args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" '
                'style="background-color:#2563eb; color:white; padding:6px 10px; '
                'border-radius:6px; text-decoration:none; box-shadow:0 2px 4px rgba(0,0,0,0.1);">'
                'Ver 📄</a>',
                download_url
            )
        return '-'
    view_pdf.short_description = 'PDF'

    def approve_engagements(self, request, queryset):
        for engagement in queryset:
            if engagement.status != 'A':
                engagement.status = 'A'
                engagement.save()
                self.send_status_email(engagement, approved=True)
        self.message_user(request, f"{queryset.count()} solicitud(es) aprobada(s).")
    approve_engagements.short_description = "Aprobar solicitudes"

    def reject_engagements(self, request, queryset):
        for engagement in queryset:
            if engagement.status != 'R':
                engagement.status = 'R'
                engagement.save()
                self.send_status_email(engagement, approved=False)
        self.message_user(request, f"{queryset.count()} solicitud(es) rechazada(s).")
    reject_engagements.short_description = "Rechazar solicitudes"

    def send_status_email(self, engagement, approved):
        subject = f"{'Aprobación' if approved else 'Actualización'} de tu solicitud de adopción"
        
        if approved:
            message = f"""
Hola {engagement.user.username},

¡Excelentes noticias! Tu solicitud de adopción para {engagement.animal.name} ha sido APROBADA.

Pronto nos pondremos en contacto contigo para continuar con el proceso.

Gracias por tu interés en ayudar a nuestros animales.

Saludos,
El equipo de la fundación
            """
        else:
            message = f"""
Hola {engagement.user.username},

Lamentamos informarte que tu solicitud de adopción para {engagement.animal.name} no ha sido aprobada en este momento.

Si tienes preguntas, no dudes en contactarnos.

Gracias por tu interés.

Saludos,
El equipo de la fundación
            """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [engagement.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando email: {e}")

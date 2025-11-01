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
        """Displays form data in a readable format"""
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
    """Envía un correo al usuario informando el estado de su solicitud"""
    
    # Determinar tipo de engagement para el mensaje
    engagement_name = engagement.get_engagements_type_display()
    
    if approved:
        subject = f'✅ ¡Tu solicitud de {engagement_name.lower()} ha sido aprobada!'
        
        if engagement.engagements_type == 'A':  # Adopción
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
        else:  # Apadrinamiento
            message = f"""
Hola {engagement.user.username},

¡Excelentes noticias! 💜

Tu solicitud de apadrinamiento para {engagement.animal.name} ha sido APROBADA.

Detalles de tu apadrinamiento:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Animal: {engagement.animal.name}
- Raza: {engagement.animal.breed.name}
- Aporte mensual: ${engagement.amount:,.0f} COP
- Fecha de solicitud: {engagement.created_at.strftime('%d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¿Qué sigue?
1. Recibirás instrucciones de pago en las próximas 24 horas
2. Te enviaremos actualizaciones mensuales sobre {engagement.animal.name}
3. Tendrás acceso a fotos y videos exclusivos de tu ahijad@

¡Gracias por tu generosidad y compromiso con {engagement.animal.name}! 🐾

Saludos cordiales,
El equipo de la Fundación
            """
    else:
        subject = f'Actualización sobre tu solicitud de {engagement_name.lower()}'
        
        message = f"""
Hola {engagement.user.username},

Gracias por tu interés en {engagement_name.lower().replace('ó', 'o')} a {engagement.animal.name}.

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
        print(f"✅ Email enviado exitosamente a {engagement.user.email}")
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from .models import AnimalEngagement

@admin.register(AnimalEngagement)
class AnimalEngagementAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'animal', 'shelter_display', 'engagement_type_badge', 'status_badge', 'created_at', 'view_pdf']
    list_filter = ['engagements_type', 'status', 'created_at', 'animal__shelter']
    search_fields = ['user__username', 'user__email', 'animal__name', 'animal__shelter__name']
    readonly_fields = ['created_at', 'updated_at', 'pdf_file', 'form_data_display', 'user', 'animal', 'engagements_type']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('user', 'animal', 'engagements_type', 'status')
        }),
        ('Detalles de la solicitud', {
            'fields': ('form_data_display', 'amount', 'pdf_file', 'admin_notes')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_engagements', 'reject_engagements']

    def shelter_display(self, obj):
        """Show the animal's shelter"""
        return obj.animal.shelter.name
    shelter_display.short_description = 'Albergue'
    
    def get_queryset(self, request):
        """Filter engagements based on user role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or request.user.is_superadmin():
            return qs
        
        if request.user.is_shelter_admin() and request.user.shelter:
            return qs.filter(animal__shelter=request.user.shelter)
        
        return qs.none()
    
    def has_add_permission(self, request):
        """Only regular users can create engagements"""
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
        if obj.form_data:
            html = "<table style='width:100%; border-collapse: collapse;'>"
            for key, value in obj.form_data.items():
                html += f"<tr style='border-bottom: 1px solid #ddd;'>"
                html += f"<td style='padding: 8px; font-weight: bold;'>{key.replace('_', ' ').title()}:</td>"
                html += f"<td style='padding: 8px;'>{value if value else 'N/A'}</td>"
                html += "</tr>"
            html += "</table>"
            return format_html(html)
        return "There is no data."
    form_data_display.short_description = 'Form data'

    def engagement_type_badge(self, obj):
        """Badge color-coded according to the type of engagement"""
        colors = {
            'A': '#10b981',  
            'S': '#9333EA',  
            'D': '#f59e0b'  
        }
        color = colors.get(obj.engagements_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_engagements_type_display()
        )
    engagement_type_badge.short_description = 'Tipo'

    def status_badge(self, obj):
        """Badge color according to state"""
        colors = {
            'P': '#f59e0b', 
            'A': '#10b981',  
            'R': '#ef4444'   
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def view_pdf(self, obj):
        """Stylish link to view/download the PDF"""
        if obj.pdf_file:
            download_url = reverse('download_pdf', args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" '
                'style="background-color:#2563eb; color:white; padding:6px 10px; '
                'border-radius:6px; text-decoration:none; box-shadow:0 2px 4px rgba(0,0,0,0.1);">'
                '📄 Ver PDF</a>',
                download_url
            )
        return '-'
    view_pdf.short_description = 'PDF'

    def approve_engagements(self, request, queryset):
        """Mass action to approve applications"""
        for engagement in queryset:
            if engagement.status != 'A':
                engagement.status = 'A'
                engagement.save()
                self.send_status_email(engagement, approved=True)
        
        self.message_user(request, f"{queryset.count()} solicitud(es) aprobada(s) exitosamente.")
    approve_engagements.short_description = "Aprobar solicitudes seleccionadas"

    def reject_engagements(self, request, queryset):
        """Mass action to reject applications"""
        for engagement in queryset:
            if engagement.status != 'R':
                engagement.status = 'R'
                engagement.save()
                self.send_status_email(engagement, approved=False)
        
        self.message_user(request, f"{queryset.count()} solicitud(es) rechazada(s).")
    reject_engagements.short_description = "Rechazar solicitudes seleccionadas"

    def send_status_email(self, engagement, approved):  
        """Send an email to the user informing them of the status of their request"""
        
        engagement_name = engagement.get_engagements_type_display()
        
        if approved:
            subject = f'¡Tu solicitud de {engagement_name.lower()} ha sido aprobada!'
            
            if engagement.engagements_type == 'A':
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
                amount_text = f"${engagement.amount:,.0f} COP" if engagement.amount else "A definir"
                message = f"""
Hola {engagement.user.username},

¡Excelentes noticias!

Tu solicitud de apadrinamiento para {engagement.animal.name} ha sido APROBADA.

Detalles de tu apadrinamiento:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Animal: {engagement.animal.name}
- Raza: {engagement.animal.breed.name}
- Aporte mensual: {amount_text}
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
            subject = f'Actualización sobre tu solicitud de {engagement_name.lower()}'
            
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
            print(f"Error sending email:{e}")
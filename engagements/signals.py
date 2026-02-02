from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import AnimalEngagement


@receiver(pre_save, sender=AnimalEngagement)
def track_status_change(sender, instance, **kwargs):
    """
    Guarda el estado anterior antes de guardar para detectar cambios
    """
    if instance.pk:
        try:
            instance._previous_status = AnimalEngagement.objects.get(pk=instance.pk).status
        except AnimalEngagement.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=AnimalEngagement)
def send_status_change_email(sender, instance, created, **kwargs):
    """
    Envía correo cuando el estado cambia a Aprobada o Rechazada
    """
    if created:
        return

    previous_status = getattr(instance, "_previous_status", None)
    current_status = instance.status

    if previous_status and previous_status != current_status and current_status in ["A", "R"]:
        send_engagement_status_email(instance, approved=(current_status == "A"))


def send_engagement_status_email(engagement, approved):
    """
    Función auxiliar para enviar el correo de cambio de estado
    """
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

¡Excelentes noticias! 💜

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
        print(f"Email enviado exitosamente a {engagement.user.email}")
    except Exception as e:
        print(f"Error enviando email: {e}")

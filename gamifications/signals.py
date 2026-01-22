from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import IntegrityError

from engagements.models import AnimalEngagement

from .models import CareIndicator, Wallet

@receiver(post_save, sender=AnimalEngagement)
def create_care_indicator_on_sponsorship_approval(sender, instance, created, **kwargs):
    """
    When a sponsorship is approved (engagements_type='S', status='A'),
    it automatically creates a CareIndicator with all indicators at 100%.
    """
    if instance.engagements_type != "S":
        return
    if instance.status != "A":
        return

    if CareIndicator.objects.filter(engagement=instance).exists():
        print(f"CareIndicator ya existe para {instance.user.username} → {instance.animal.name}")
        return
    
    try:
        care_indicator = CareIndicator.objects.create(
            engagement=instance, 
            food_level=100, 
            hygiene_level=100, 
            health_level=100
        )
        print(f"✓ CareIndicator creado para {instance.user.username} → {instance.animal.name}")

    except IntegrityError as e:
        print(f"CareIndicator ya existía (race condition): {e}")
    except Exception as e:
        print(f"Error creando CareIndicator: {e}")


@receiver(post_save, sender=AnimalEngagement)
def ensure_user_has_wallet_for_shelter(sender, instance, created, **kwargs):
    """
    When a sponsorship (S+A) is approved, ensure that the user
    has a wallet for that hostel with 0 coins.
    """
    if instance.engagements_type != 'S':
        return
    if instance.status != 'A':
        return
    
    shelter = instance.animal.shelter
    
    wallet, wallet_created = Wallet.objects.get_or_create(
        user=instance.user,
        shelter=shelter,
        defaults={
            'balance': 0,
            'total_earned': 0,
            'total_spent': 0,
        }
    )
    
    if wallet_created:
        print(f"✓ Wallet creada para {instance.user.username} en {shelter.name}")
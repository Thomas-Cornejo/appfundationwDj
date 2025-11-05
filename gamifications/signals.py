from django.db.models.signals import post_save
from django.dispatch import receiver
from engagements.models import AnimalEngagement
from .models import CareIndicator, VirtualWallet

@receiver(post_save, sender=AnimalEngagement)
def create_care_indicator_on_sponsorship_approval(sender, instance, created, **kwargs):
    """
    Cuando se APRUEBA un apadrinamiento (engagements_type='S', status='A'),
    crea automáticamente un CareIndicator con todos los indicadores en 100%.
    """
    if instance.engagements_type != 'S':
        return
    if instance.status != 'A':
        return
    
    if hasattr(instance, 'care_indicator'):
        print(f"CareIndicator ya existe para {instance.user.username} → {instance.animal.name}")
        return
    try:
        care_indicator = CareIndicator.objects.create(
            engagement=instance,
            food_level=100,
            hygiene_level=100,
            health_level=100
        )
        print(f"CareIndicator creado: {instance.user.username} → {instance.animal.name}")
        
        
    except Exception as e:
        print(f"Error creando CareIndicator: {e}")

@receiver(post_save, sender=CareIndicator)
def ensure_user_has_wallet(sender, instance, created, **kwargs):
    """
    Cuando se crea un CareIndicator (usuario está apadrinando),
    asegura que el usuario tenga una VirtualWallet.
    Si no existe, la crea con 1000 monedas iniciales.
    """
    
    if not created:
        return
    
    user = instance.user
    
    if hasattr(user, 'wallet'):
        print(f"{user.username} ya tiene una VirtualWallet con {user.wallet.balance} monedas")
        return
    try:
        wallet = VirtualWallet.objects.create(
            user=user,
            balance=1000 
        )
        print(f"VirtualWallet creada para {user.username} con {wallet.balance} monedas")
        
        from .models import WalletTransaction
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='E', 
            amount=1000,
            description="Bienvenida - Primera recarga"
        )
        print(f"Transacción inicial registrada para {user.username}")
        
    except Exception as e:
        print(f"Error creando VirtualWallet: {e}")
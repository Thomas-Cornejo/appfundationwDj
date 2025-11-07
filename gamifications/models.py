from django.db import models
from django.conf import settings
from django.utils import timezone
from animals.models import Animal
from engagements.models import AnimalEngagement

# Create your models here.

class CareIndicator(models.Model):
    """
    Indicadores de cuidado para un animal apadrinado.
    Cada engagement aprobado de tipo 'S' (Sponsorship) tiene un CareIndicator.
    """
    
    engagement = models.OneToOneField(
        AnimalEngagement,
        on_delete=models.CASCADE,
        related_name='care_indicator',
        verbose_name="Apadrinamiento"
    )
    
    food_level = models.IntegerField(
        default=100,
        verbose_name="Nivel de alimentación (%)",
        help_text="0 = Hambriento, 100 = Bien alimentado"
    )
    hygiene_level = models.IntegerField(
        default=100,
        verbose_name="Nivel de higiene (%)",
        help_text="0 = Sucio, 100 = Limpio"
    )
    health_level = models.IntegerField(
        default=100,
        verbose_name="Nivel de salud (%)",
        help_text="0 = Enfermo, 100 = Saludable"
    )

    last_food_update = models.DateTimeField(default=timezone.now)
    last_hygiene_update = models.DateTimeField(default=timezone.now)
    last_health_update = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Indicador de Cuidado"
        verbose_name_plural = "Indicadores de Cuidado"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.engagement.user.username} → {self.engagement.animal.name}"
    
    @property
    def animal(self):
        """Atajo para acceder al animal"""
        return self.engagement.animal
    
    @property
    def user(self):
        """Atajo para acceder al usuario (padrino)"""
        return self.engagement.user
    
    @property
    def shelter(self):
        """Atajo para acceder al albergue"""
        return self.engagement.animal.shelter
    
    @property
    def overall_status(self):
        """Retorna el estado general promedio (0-100)"""
        return round((self.food_level + self.hygiene_level + self.health_level) / 3)
    
    def get_status_color(self):
        """Retorna color según el estado general"""
        status = self.overall_status
        if status >= 70:
            return 'green'  
        elif status >= 40:
            return 'yellow'  
        else:
            return 'red'  
    
    def needs_attention(self):
        """Verifica si algún indicador está crítico (<30%)"""
        return (
            self.food_level < 30 or 
            self.hygiene_level < 30 or 
            self.health_level < 30
        )
    
    def apply_degradation(self):
        """
        Aplica degradación automática según configuración del shelter.
        Este método será llamado por un cron job o celery task periódicamente.
        """
        shelter = self.shelter
        now = timezone.now()
        changed = False
        
        hours_since_food = (now - self.last_food_update).total_seconds() / 3600
        if hours_since_food >= shelter.food_degradation_hours:
            cycles = int(hours_since_food / shelter.food_degradation_hours)
            degradation = shelter.food_degradation_percentage * cycles
            self.food_level = max(0, self.food_level - degradation)
            self.last_food_update = now
            changed = True
        
        hours_since_hygiene = (now - self.last_hygiene_update).total_seconds() / 3600
        if hours_since_hygiene >= shelter.hygiene_degradation_hours:
            cycles = int(hours_since_hygiene / shelter.hygiene_degradation_hours)
            degradation = shelter.hygiene_degradation_percentage * cycles
            self.hygiene_level = max(0, self.hygiene_level - degradation)
            self.last_hygiene_update = now
            changed = True
        
        if self.food_level < 30 or self.hygiene_level < 30:
            self.health_level = max(0, self.health_level - 5)
            self.last_health_update = now
            changed = True
        
        if changed:
            self.save()
        
        return changed

class CareAction(models.Model):
    """
    Registro de cada acción de cuidado que realiza un usuario.
    Permite llevar historial y calcular estadísticas.
    """
    
    ACTION_TYPES = [
        ('F', 'Feed'),     
        ('H', 'Hygiene'),   
        ('M', 'Medical'),   
    ]
    
    care_indicator = models.ForeignKey(
        CareIndicator,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name="Indicador de cuidado"
    )
    
    action_type = models.CharField(
        max_length=1,
        choices=ACTION_TYPES,
        verbose_name="Tipo de acción"
    )
    
    amount_increased = models.IntegerField(
        verbose_name="Cantidad aumentada (%)",
        help_text="Cuánto subió el indicador"
    )
    
    coins_spent = models.IntegerField(
        default=0,
        verbose_name="Monedas gastadas"
    )
    
    xp_earned = models.IntegerField(
        default=0,
        verbose_name="XP ganado"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Acción de Cuidado"
        verbose_name_plural = "Acciones de Cuidado"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.care_indicator.animal.name} (+{self.amount_increased}%)"
    
    @property
    def user(self):
        """Usuario que realizó la acción"""
        return self.care_indicator.user
    
    @property
    def animal(self):
        """Animal que fue cuidado"""
        return self.care_indicator.animal

class VirtualWallet(models.Model):
    """
    Billetera virtual del usuario con monedas para gastar en cuidados.
    Cada usuario tiene UNA billetera.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name="Usuario"
    )
    
    balance = models.IntegerField(
        default=1000, 
        verbose_name="Saldo de monedas"
    )
    
    total_earned = models.IntegerField(
        default=0,
        verbose_name="Total ganado (histórico)"
    )
    
    total_spent = models.IntegerField(
        default=0,
        verbose_name="Total gastado (histórico)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Billetera Virtual"
        verbose_name_plural = "Billeteras Virtuales"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.balance} monedas"
    
    def add_coins(self, amount, description=""):
        """Agregar monedas a la billetera"""
        if amount <= 0:
            return False
        
        self.balance += amount
        self.total_earned += amount
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='E',
            amount=amount,
            description=description or "Monedas agregadas"
        )
        
        return True
    
    def spend_coins(self, amount, description=""):
        """Gastar monedas (verifica saldo)"""
        if amount <= 0:
            return False
        
        if self.balance < amount:
            return False 
        self.balance -= amount
        self.total_spent += amount
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='S',
            amount=amount,
            description=description or "Monedas gastadas"
        )
        
        return True
    
    def can_afford(self, amount):
        """Verifica si tiene suficiente saldo"""
        return self.balance >= amount
    
class WalletTransaction(models.Model):
    """
    Registro de todas las transacciones de monedas.
    Permite auditoría y estadísticas.
    """
    
    TRANSACTION_TYPES = [
        ('E', 'Earn'),  
        ('S', 'Spend'),  
    ]
    
    wallet = models.ForeignKey(
        VirtualWallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Billetera"
    )
    
    transaction_type = models.CharField(
        max_length=1,
        choices=TRANSACTION_TYPES,
        verbose_name="Tipo"
    )
    
    amount = models.IntegerField(verbose_name="Cantidad")
    
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descripción"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transacción de Billetera"
        verbose_name_plural = "Transacciones de Billetera"
        ordering = ['-created_at']
    
    def __str__(self):
        symbol = '+' if self.transaction_type == 'E' else '-'
        return f"{self.wallet.user.username}: {symbol}{self.amount} - {self.description}"
    
    @property
    def is_earn(self):
        """Verifica si es ingreso"""
        return self.transaction_type == 'E'
    
    @property
    def is_spend(self):
        """Verifica si es gasto"""
        return self.transaction_type == 'S'
    
class WalletRecharge(models.Model):
    """
    Registro de recargas de dinero real a la billetera virtual.
    Cada recarga es una DONACIÓN a la fundación.
    """
    
    PAYMENT_METHODS = [
        ('PSE', 'PSE'),
        ('CARD', 'Tarjeta de Crédito/Débito'),
        ('TRANSFER', 'Transferencia Bancaria'),
        ('CASH', 'Efectivo'),
    ]
    
    STATUS_CHOICES = [
        ('P', 'Pending'),      
        ('A', 'Approved'),     
        ('R', 'Rejected'),     
        ('F', 'Failed'),       
        ]
    
    wallet = models.ForeignKey(
        VirtualWallet,
        on_delete=models.CASCADE,
        related_name='recharges',
        verbose_name="Billetera"
    )
    
    amount_cop = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto en COP",
        help_text="Dinero real donado"
    )
    
    coins_received = models.IntegerField(
        verbose_name="Monedas recibidas",
        help_text="Monedas virtuales a agregar (1 COP = 0.1 monedas)"
    )
    
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        verbose_name="Método de pago"
    )
    
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='P',
        verbose_name="Estado"
    )
    
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID de transacción externa",
        help_text="ID del banco o pasarela de pago"
    )
    
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Referencia de pago"
    )
    
    shelter = models.ForeignKey(
        'shelters.Shelter',
        on_delete=models.CASCADE,
        related_name='recharges',
        verbose_name="Albergue destino",
        help_text="La donación va a este albergue"
    )
    
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas del administrador"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Recarga de Billetera"
        verbose_name_plural = "Recargas de Billetera"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.user.username} - ${self.amount_cop} → {self.coins_received} monedas [{self.get_status_display()}]"
    
    def approve(self):
        """Aprobar la recarga y agregar monedas a la billetera"""
        if self.status != 'A':
            self.status = 'A'
            self.approved_at = timezone.now()
            self.save()
            
            self.wallet.add_coins(
                amount=self.coins_received,
                description=f"Recarga aprobada: ${self.amount_cop} COP"
            )
            
            return True
        return False
    
    def reject(self, reason=""):
        """Rechazar la recarga"""
        self.status = 'R'
        if reason:
            self.admin_notes = reason
        self.save()
        return True
    
    @staticmethod
    def calculate_coins(amount_cop):
        """
        Calcula las monedas según el monto en COP.
        Tasa: 1 COP = 0.1 monedas (o sea, 10 COP = 1 moneda)
        """
        return int(amount_cop / 10)
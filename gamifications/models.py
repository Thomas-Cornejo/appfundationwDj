from django.db import models
from django.conf import settings
from django.utils import timezone
from animals.models import Animal
from engagements.models import AnimalEngagement

# Create your models here.

class CareIndicator(models.Model):
    """
    Care indicators for a sponsored animal.
    Each approved 'S' (Sponsorship) engagement has a CareIndicator.
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
        """Shortcut to access the animal"""
        return self.engagement.animal
    
    @property
    def user(self):
        """Shortcut to access the user (godfather)"""
        return self.engagement.user
    
    @property
    def shelter(self):
        """Shortcut to access the hostel"""
        return self.engagement.animal.shelter
    
    @property
    def overall_status(self):
        """Returns the average overall state (0-100)"""
        return round((self.food_level + self.hygiene_level + self.health_level) / 3)
    
    def get_status_color(self):
        """Returns color according to the overall condition"""
        status = self.overall_status
        if status >= 70:
            return 'green'  
        elif status >= 40:
            return 'yellow'  
        else:
            return 'red'  
    
    def needs_attention(self):
        """Check if any indicator is critical (<30%)"""
        return (
            self.food_level < 30 or 
            self.hygiene_level < 30 or 
            self.health_level < 30
        )
    
    def apply_degradation(self):
        """
        Automatic downgrade based on shelter configuration.
        This method will be called periodically by a cron job or Celery task.
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
    Record of every care action performed by a user.
    Allows for tracking history and calculating statistics. 
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
    The user's virtual wallet contains coins to spend on care.
    Each user has one wallet.
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
        """Spend coins (check balance)"""
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
        """Check if you have enough balance"""
        return self.balance >= amount
    
class WalletTransaction(models.Model):
    """
    Record of all currency transactions.
    Enables auditing and statistics.
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
    Record of real money top-ups to the virtual wallet.
    Each top-up is a DONATION to the foundation.
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
        """Approve the top-up and add coins to the wallet"""
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
        """Reject the recharge"""
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

class CoinUsage(models.Model):
    """
    It records every time coins are used and which hostel they go to.
    It allows you to track the distribution of funds.
    """
    wallet = models.ForeignKey(
        'VirtualWallet',
        on_delete=models.CASCADE,
        related_name='coin_usages'
    )
    shelter = models.ForeignKey(
        'shelters.Shelter',
        on_delete=models.CASCADE,
        related_name='coin_usages'
    )
    animal = models.ForeignKey(
        'animals.Animal',
        on_delete=models.CASCADE,
        related_name='coin_usages'
    )
    care_action = models.ForeignKey(
        'CareAction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coin_usage'
    )
    
    coins_used = models.IntegerField(verbose_name="Monedas usadas")
    amount_cop = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Equivalente en COP"
    )
    
    action_type = models.CharField(
        max_length=10,
        choices=[
            ('FEED', 'Alimentar'),
            ('CLEAN', 'Limpiar'),
            ('HEALTH', 'Salud'),
        ],
        verbose_name="Tipo de acción"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Uso de Monedas"
        verbose_name_plural = "Usos de Monedas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shelter', 'created_at']),
            models.Index(fields=['wallet', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.coins_used} monedas → {self.shelter.name} ({self.get_action_type_display()})"


class MonthlyDistribution(models.Model):
    """
    Monthly distribution record for shelters.
    It is automatically calculated based on the month's CoinUsage.
    """
    shelter = models.ForeignKey(
        'shelters.Shelter',
        on_delete=models.CASCADE,
        related_name='monthly_distributions'
    )
    
    month = models.DateField(
        verbose_name="Mes de distribución",
        help_text="Primer día del mes correspondiente"
    )
    
    total_coins_used = models.IntegerField(
        default=0,
        verbose_name="Monedas usadas en el mes"
    )
    
    amount_cop = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto en COP"
    )
    
    STATUS_CHOICES = [
        ('P', 'Pendiente'),
        ('PR', 'Procesando'),
        ('PA', 'Pagado'),
        ('F', 'Fallido'),
    ]
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default='P',
        verbose_name="Estado"
    )
    
    wompi_payout_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID del desembolso en Wompi"
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Mensaje de error",
        help_text="Si el pago falló, aquí se guarda el motivo"
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de pago"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Monthly Distribution"
        verbose_name_plural = "Monthly Distributions"
        unique_together = ['shelter', 'month']
        ordering = ['-month', 'shelter']
        indexes = [
            models.Index(fields=['month', 'status']),
            models.Index(fields=['shelter', 'month']),
        ]
    
    def __str__(self):
        return f"{self.shelter.name} - {self.month.strftime('%B %Y')} - ${self.amount_cop:,.0f}"
    
    def mark_as_paid(self, payout_id):
        """Mark as paid successfully"""
        self.status = 'PA'
        self.wompi_payout_id = payout_id
        self.paid_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark as failed"""
        self.status = 'F'
        self.error_message = error_message
        self.save()


class DirectPayment(models.Model):
    """
    Direct payments to shelters (for medical emergencies).
    They do not go through the virtual currency system.
    The money goes directly to the shelter immediately.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_payments'
    )
    history = models.ForeignKey(
        'animals.History',
        on_delete=models.CASCADE,
        related_name='direct_payments',
        help_text="Evento médico al que se contribuye"
    )
    shelter = models.ForeignKey(
        'shelters.Shelter',
        on_delete=models.CASCADE,
        related_name='direct_payments'
    )
    
    amount_cop = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto en COP"
    )
    
    STATUS_CHOICES = [
        ('P', 'Pendiente'),
        ('A', 'Aprobado'),
        ('T', 'Transferido'),
        ('R', 'Rechazado'),
    ]
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='P',
        verbose_name="Estado"
    )
    
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Referencia de pago"
    )
    
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID de transacción Wompi"
    )
    
    transferred_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de transferencia"
    )
    
    transfer_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Referencia de transferencia",
        help_text="Referencia del pago al albergue"
    )
    
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas del administrador"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pago Directo"
        verbose_name_plural = "Pagos Directos"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} → {self.shelter.name} - ${self.amount_cop:,.0f}"
    
    def mark_as_transferred(self, reference, notes=""):
        """Marcar como transferido al albergue"""
        self.status = 'T'
        self.transferred_at = timezone.now()
        self.transfer_reference = reference
        if notes:
            self.admin_notes = notes
        self.save()

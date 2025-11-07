from django.db import models

class Shelter(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre del albergue")
    email = models.CharField(max_length=255, verbose_name="Email del albergue")
    description = models.TextField(blank=True, null=True, verbose_name="Descripcion")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    food_unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=2000, verbose_name="Costo unitario del alimento (COP)")
    hygiene_unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=2000, verbose_name="Costo unitario de la higiene (COP)")
    food_degradation_hours = models.SmallIntegerField(default=8, verbose_name="Horas para degradacion del alimento") 
    food_degradation_percentage = models.SmallIntegerField(default=10, verbose_name="Porcentaje de degradacion del alimento")
    hygiene_degradation_hours = models.SmallIntegerField(default=24, verbose_name="Horas para degradacion de la higiene")
    hygiene_degradation_percentage = models.SmallIntegerField(default=10, verbose_name="Porcentaje de degradacion de la higiene")
    
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('NEQUI', 'Nequi'),
            ('BANK', 'Cuenta Bancaria'),
            ('WOMPI', 'Cuenta Wompi'),
        ],
        default='NEQUI',
        verbose_name="Método de pago preferido"
    )
    
    nequi_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono Nequi",
        help_text="Número Nequi para recibir pagos (ej: 3001234567)"
    )
    
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nombre del banco",
        help_text="Bancolombia, Davivienda, etc."
    )
    
    bank_account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número de cuenta"
    )
    
    bank_account_type = models.CharField(
        max_length=20,
        choices=[
            ('SAVINGS', 'Ahorros'),
            ('CHECKING', 'Corriente'),
        ],
        blank=True,
        null=True,
        verbose_name="Tipo de cuenta"
    )
    
    wompi_merchant_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Merchant ID de Wompi",
        help_text="Si el albergue tiene cuenta Wompi verificada"
    )
    
    legal_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Razón social",
        help_text="Nombre legal/comercial para transferencias"
    )
    
    identification_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="NIT o Cédula",
        help_text="Número de identificación tributaria"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Albergue"
        verbose_name_plural = "Albergues"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_total_animals(self):
        """The total number of active animals at the shelter returns"""
        return self.animals.filter(is_active=True).count()
    
    def get_animals_for_adoption(self):
        """Return animals available for adoption"""
        return self.animals.filter(is_active=True, availability__in=['A', 'B']).count()
    
    def get_animals_for_sponsorship(self):
        """Return animals available for sponsorship"""
        return self.animals.filter(is_active=True, availability__in=['S', 'B']).count()
    
    def has_payment_info(self):
        """Check if the hostel has payment information set up."""
        if self.payment_method == 'NEQUI':
            return bool(self.nequi_phone)
        elif self.payment_method == 'BANK':
            return bool(self.bank_account_number and self.bank_name)
        elif self.payment_method == 'WOMPI':
            return bool(self.wompi_merchant_id)
        return False
    
    def get_payment_info_display(self):
        """Returns payment information formatted for display"""
        if self.payment_method == 'NEQUI':
            return f"Nequi: {self.nequi_phone}"
        elif self.payment_method == 'BANK':
            return f"{self.bank_name} - {self.bank_account_number} ({self.get_bank_account_type_display()})"
        elif self.payment_method == 'WOMPI':
            return f"Wompi Merchant: {self.wompi_merchant_id}"
        return "Sin configurar"

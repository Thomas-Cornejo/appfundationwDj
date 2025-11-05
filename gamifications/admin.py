from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Sum, Count
from django.utils import timezone
from .models import (
    CareIndicator, 
    CareAction, 
    VirtualWallet, 
    WalletTransaction, 
    WalletRecharge
)

# ============================================
# ADMIN 1: CARE INDICATOR
# ============================================

@admin.register(CareIndicator)
class CareIndicatorAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user_display',
        'animal_display',
        'shelter_display',
        'food_badge',
        'hygiene_badge',
        'health_badge',
        'overall_badge',
        'needs_attention_icon',
        'has_health_events_icon',
        'created_at'
    ]
    
    list_filter = [
        'engagement__animal__shelter',
        'created_at',
    ]
    
    search_fields = [
        'engagement__user__username',
        'engagement__animal__name',
        'engagement__animal__shelter__name'
    ]
    
    readonly_fields = [
        'engagement',
        'created_at',
        'updated_at',
        'last_food_update',
        'last_hygiene_update',
        'last_health_update',
        'overall_status',
        'get_status_color'
    ]
    
    fieldsets = (
        ('Información del Apadrinamiento', {
            'fields': ('engagement',)
        }),
        ('Indicadores Actuales', {
            'fields': (
                ('food_level', 'last_food_update'),
                ('hygiene_level', 'last_hygiene_update'),
                ('health_level', 'last_health_update'),
            ),
            'description': 'Niveles actuales de cada indicador (0-100%). Comida e higiene se degradan automáticamente. Salud solo baja con eventos médicos.'
        }),
        ('Estado General', {
            'fields': ('overall_status', 'get_status_color'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_indicators']
    
    def user_display(self, obj):
        """Muestra el usuario (padrino)"""
        try:
            return obj.user.username
        except Exception as e:
            return f"Error: {str(e)}"
    user_display.short_description = 'Usuario'
    
    def animal_display(self, obj):
        """Muestra el animal"""
        try:
            return obj.animal.name
        except Exception as e:
            return f"Error: {str(e)}"
    animal_display.short_description = 'Animal'
    
    def shelter_display(self, obj):
        """Muestra el albergue"""
        try:
            return obj.shelter.name
        except Exception as e:
            return f"Error: {str(e)}"
    shelter_display.short_description = 'Albergue'
    
    def food_badge(self, obj):
        """Badge colorizado para nivel de comida"""
        try:
            return self._create_level_badge(obj.food_level, '🍖')
        except Exception as e:
            return f"Error: {str(e)}"
    food_badge.short_description = 'Comida'
    
    def hygiene_badge(self, obj):
        """Badge colorizado para nivel de higiene"""
        try:
            return self._create_level_badge(obj.hygiene_level, '🧼')
        except Exception as e:
            return f"Error: {str(e)}"
    hygiene_badge.short_description = 'Higiene'
    
    def health_badge(self, obj):
        """Badge colorizado para nivel de salud"""
        try:
            return self._create_level_badge(obj.health_level, '❤️')
        except Exception as e:
            return f"Error: {str(e)}"
    health_badge.short_description = 'Salud'
    
    def overall_badge(self, obj):
        """Badge para estado general"""
        try:
            status = obj.overall_status
            color = self._get_color_by_level(status)
            return format_html(
                '<span style="background-color: {}; color: white; padding: 4px 12px; '
                'border-radius: 12px; font-weight: bold; font-size: 11px;">{:.0f}%</span>',
                color, 
                status
            )
        except Exception as e:
            return f"Error: {str(e)}"
    overall_badge.short_description = 'Estado General'
    
    def needs_attention_icon(self, obj):
        """Icono de alerta si necesita atención"""
        try:
            if obj.needs_attention():
                return format_html(
                    '<span style="font-size: 20px;" title="¡Necesita atención urgente!">⚠️</span>'
                )
            return format_html('<span style="color: green; font-size: 16px;">✓</span>')
        except Exception as e:
            return f"Error: {str(e)}"
    needs_attention_icon.short_description = 'Alerta'
    
    def has_health_events_icon(self, obj):
        """Muestra si el animal tiene eventos de salud pendientes"""
        try:
            from animals.models import History
            
            pending_events = History.objects.filter(
                animal=obj.animal,
                status__in=['P', 'T'],
                cost_coins__gt=0
            ).count()
            
            if pending_events > 0:
                return format_html(
                    '<span style="font-size: 18px;" title="{} evento(s) de salud activo(s)">🏥 {}</span>',
                    pending_events,
                    pending_events
                )
            return format_html('<span style="color: green;">-</span>')
        except Exception as e:
            return f"Error: {str(e)}"
    has_health_events_icon.short_description = '🏥 Eventos'
    
    def _create_level_badge(self, level, icon):
        """Crea un badge colorizado según el nivel"""
        try:
            level = int(level) if level is not None else 0
            color = self._get_color_by_level(level)
            
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 10px; '
                'border-radius: 10px; font-size: 11px;">{} {}%</span>',
                color, 
                icon, 
                level
            )
        except Exception as e:
            return format_html(
                '<span style="color: red;">Error: {}</span>',
                str(e)
            )
    
    def _get_color_by_level(self, level):
        """Retorna color según el nivel"""
        try:
            level = int(level) if level is not None else 0
            if level >= 70:
                return '#10b981' 
            elif level >= 40:
                return '#f59e0b'
            else:
                return '#ef4444' 
        except:
            return '#6b7280' 
    def reset_indicators(self, request, queryset):
        """Resetea todos los indicadores a 100%"""
        try:
            count = queryset.count()
            queryset.update(
                food_level=100,
                hygiene_level=100,
                health_level=100,
                last_food_update=timezone.now(),
                last_hygiene_update=timezone.now(),
                last_health_update=timezone.now()
            )
            self.message_user(
                request, 
                f'{count} indicador(es) reseteado(s) al 100%%.'
            )
        except Exception as e:
            self.message_user(
                request, 
                f'Error al resetear: {str(e)}', 
                level='error'
            )
    reset_indicators.short_description = 'Resetear al 100%%'
    
    def get_queryset(self, request):
        """Filtrar según permisos"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return qs
        
        if hasattr(request.user, 'is_shelter_admin') and request.user.is_shelter_admin():
            if hasattr(request.user, 'shelter') and request.user.shelter:
                return qs.filter(engagement__animal__shelter=request.user.shelter)
        
        return qs.none()


# ============================================
# ADMIN 2: CARE ACTION
# ============================================

@admin.register(CareAction)
class CareActionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'created_at',
        'user_display',
        'animal_display',
        'action_badge',
        'amount_increased',
        'coins_spent',
        'xp_earned'
    ]
    
    list_filter = [
        'action_type',
        'created_at',
        'care_indicator__engagement__animal__shelter'
    ]
    
    search_fields = [
        'care_indicator__engagement__user__username',
        'care_indicator__engagement__animal__name'
    ]
    
    readonly_fields = [
        'care_indicator',
        'action_type',
        'amount_increased',
        'coins_spent',
        'xp_earned',
        'created_at'
    ]
    
    fieldsets = (
        ('Información de la Acción', {
            'fields': ('care_indicator', 'action_type', 'created_at')
        }),
        ('Detalles', {
            'fields': ('amount_increased', 'coins_spent', 'xp_earned')
        }),
    )
    
    def user_display(self, obj):
        """Usuario que realizó la acción"""
        return obj.user.username
    user_display.short_description = 'Usuario'
    
    def animal_display(self, obj):
        """Animal que fue cuidado"""
        return obj.animal.name
    animal_display.short_description = 'Animal'
    
    def action_badge(self, obj):
        """Badge colorizado según el tipo de acción"""
        colors = {
            'F': '#10b981', 
            'H': '#3b82f6', 
            'M': '#ef4444', 
        }
        icons = {
            'F': '🍖',
            'H': '🧼',
            'M': '💊'
        }
        color = colors.get(obj.action_type, '#6b7280')
        icon = icons.get(obj.action_type, '❓')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{} {}</span>',
            color, icon, obj.get_action_type_display()
        )
    action_badge.short_description = 'Tipo'
    
    def has_add_permission(self, request):
        """No se pueden crear acciones manualmente desde el admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar acciones"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return True
        return False
    
    def get_queryset(self, request):
        """Filtrar según permisos"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return qs
        
        if hasattr(request.user, 'is_shelter_admin') and request.user.is_shelter_admin():
            if hasattr(request.user, 'shelter') and request.user.shelter:
                return qs.filter(care_indicator__engagement__animal__shelter=request.user.shelter)
        
        return qs.none()


# ============================================
# ADMIN 3: VIRTUAL WALLET
# ============================================

@admin.register(VirtualWallet)
class VirtualWalletAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'balance_display',
        'total_earned',
        'total_spent',
        'created_at'
    ]
    
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    
    readonly_fields = [
        'user',
        'balance',
        'total_earned',
        'total_spent',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Saldo Actual', {
            'fields': ('balance',)
        }),
        ('Estadísticas', {
            'fields': ('total_earned', 'total_spent')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def balance_display(self, obj):
        """Muestra el saldo con estilo"""
        color = '#10b981' if obj.balance > 0 else '#ef4444'
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">🪙 {} monedas</span>',
            color, obj.balance
        )
    balance_display.short_description = 'Saldo'
    
    def has_add_permission(self, request):
        """No se pueden crear billeteras manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar billeteras"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return True
        return False


# ============================================
# ADMIN 4: WALLET TRANSACTION
# ============================================

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'created_at',
        'user_display',
        'transaction_badge',
        'amount_display',
        'description'
    ]
    
    list_filter = [
        'transaction_type',
        'created_at'
    ]
    
    search_fields = [
        'wallet__user__username',
        'description'
    ]
    
    readonly_fields = [
        'wallet',
        'transaction_type',
        'amount',
        'description',
        'created_at'
    ]
    
    fieldsets = (
        ('Transacción', {
            'fields': ('wallet', 'transaction_type', 'amount', 'description', 'created_at')
        }),
    )
    
    def user_display(self, obj):
        """Usuario de la transacción"""
        return obj.wallet.user.username
    user_display.short_description = 'Usuario'
    
    def transaction_badge(self, obj):
        """Badge según el tipo de transacción"""
        if obj.transaction_type == 'E':
            color = '#10b981'
            icon = '💰'
            text = 'Ingreso'
        else:
            color = '#ef4444'
            icon = '💸'
            text = 'Gasto'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{} {}</span>',
            color, icon, text
        )
    transaction_badge.short_description = 'Tipo'
    
    def amount_display(self, obj):
        """Muestra el monto con signo"""
        symbol = '+' if obj.transaction_type == 'E' else '-'
        color = '#10b981' if obj.transaction_type == 'E' else '#ef4444'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, symbol, obj.amount
        )
    amount_display.short_description = 'Monto'
    
    def has_add_permission(self, request):
        """No se pueden crear transacciones manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar transacciones"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return True
        return False


# ============================================
# ADMIN 5: WALLET RECHARGE
# ============================================

@admin.register(WalletRecharge)
class WalletRechargeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'created_at',
        'user_display',
        'amount_cop',
        'coins_received',
        'payment_method',
        'status_badge',
        'shelter',
        'approve_button'
    ]
    
    list_filter = [
        'status',
        'payment_method',
        'shelter',
        'created_at'
    ]
    
    search_fields = [
        'wallet__user__username',
        'transaction_id',
        'payment_reference'
    ]
    
    readonly_fields = [
        'wallet',
        'amount_cop',
        'coins_received',
        'created_at',
        'approved_at'
    ]
    
    fieldsets = (
        ('Información de la Recarga', {
            'fields': ('wallet', 'amount_cop', 'coins_received', 'shelter')
        }),
        ('Pago', {
            'fields': ('payment_method', 'transaction_id', 'payment_reference')
        }),
        ('Estado', {
            'fields': ('status', 'admin_notes')
        }),
        ('Fechas', {
            'fields': ('created_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_recharges', 'reject_recharges']
    
    def user_display(self, obj):
        """Usuario que realizó la recarga"""
        return obj.wallet.user.username
    user_display.short_description = 'Usuario'
    
    def status_badge(self, obj):
        """Badge colorizado según el estado"""
        colors = {
            'P': '#f59e0b',  
            'A': '#10b981',  
            'R': '#ef4444',  
            'F': '#6b7280', 
        }
        color = colors.get(obj.status, '#6b7280')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def approve_button(self, obj):
        """Botón para aprobar rápidamente"""
        if obj.status == 'P':
            return format_html(
                '<a class="button" href="#" onclick="return false;" '
                'style="background-color: #10b981; color: white; padding: 5px 10px; '
                'border-radius: 5px; text-decoration: none;">Aprobar</a>'
            )
        return '-'
    approve_button.short_description = 'Acción'
    
    def approve_recharges(self, request, queryset):
        """Aprueba recargas pendientes"""
        count = 0
        for recharge in queryset.filter(status='P'):
            if recharge.approve():
                count += 1
        
        self.message_user(request, f'{count} recarga(s) aprobada(s) exitosamente.')
    approve_recharges.short_description = 'Aprobar recargas seleccionadas'
    
    def reject_recharges(self, request, queryset):
        """Rechaza recargas pendientes"""
        count = 0
        for recharge in queryset.filter(status='P'):
            if recharge.reject():
                count += 1
        
        self.message_user(request, f'{count} recarga(s) rechazada(s).')
    reject_recharges.short_description = 'Rechazar recargas seleccionadas'
    
    def get_queryset(self, request):
        """Filtrar según permisos"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return qs
        
        if hasattr(request.user, 'is_shelter_admin') and request.user.is_shelter_admin():
            if hasattr(request.user, 'shelter') and request.user.shelter:
                return qs.filter(shelter=request.user.shelter)
        
        return qs.none()
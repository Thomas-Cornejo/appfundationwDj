from django.contrib import admin
from .models import Shelter

@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'email', 'description', 'is_active')
        }),
        ('Configuración de Gamificación - Costos', {
            'fields': (
                'food_unit_cost',
                'hygiene_unit_cost',
            ),
            'description': 'Costos de las unidades para el sistema de gamificación',
            'classes': ('collapse',)  
        }),
        ('Configuración de Gamificación - Degradación', {
            'fields': (
                'food_degradation_hours',
                'food_degradation_percentage',
                'hygiene_degradation_hours',
                'hygiene_degradation_percentage',
            ),
            'description': 'Configuración de cómo se degradan los indicadores con el tiempo',
            'classes': ('collapse',) 
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter hostels by role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return qs
        
        if hasattr(request.user, 'is_shelter_admin') and request.user.is_shelter_admin():
            if hasattr(request.user, 'shelter') and request.user.shelter:
                return qs.filter(id=request.user.shelter.id)
        
        return qs.none()
    
    def has_add_permission(self, request):
        """Only Super Admins can create hostels"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return True
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete hostels"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return True
        return False
    
    def has_change_permission(self, request, obj=None):
        """Super Admin can edit everything"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin():
            return True
        return False
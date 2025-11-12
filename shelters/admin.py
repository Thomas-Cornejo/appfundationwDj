from django.contrib import admin
from django.utils.html import format_html

from .models import Shelter


@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "is_active", "payment_status", "created_at"]
    list_filter = ["is_active", "payment_method", "created_at"]
    search_fields = ["name", "email", "legal_name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Información Básica",
            {"fields": ("name", "email", "description", "is_active")},
        ),
        (
            "Información Legal y de Pago",
            {
                "fields": (
                    "legal_name",
                    "identification_number",
                    "payment_method",
                    "nequi_phone",
                    "bank_name",
                    "bank_account_type",
                    "bank_account_number",
                    "wompi_merchant_id",
                ),
            },
        ),
        (
            "Configuración de Gamificación - Costos",
            {
                "fields": (
                    "food_unit_cost",
                    "hygiene_unit_cost",
                ),
                "description": "Costos de las unidades para el sistema de gamificación",
                "classes": ("collapse",),
            },
        ),
        (
            "Configuración de Gamificación - Degradación",
            {
                "fields": (
                    "food_degradation_hours",
                    "food_degradation_percentage",
                    "hygiene_degradation_hours",
                    "hygiene_degradation_percentage",
                ),
                "description": "Configuración de cómo se degradan los indicadores con el tiempo",
                "classes": ("collapse",),
            },
        ),
        (
            "Metadatos",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def payment_status(self, obj):
        """It shows if you have configured payment information."""
        if obj.has_payment_info():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Configurado</span><br>'
                '<small style="color: #666;">{}</small>',
                obj.get_payment_info_display(),
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Sin configurar</span><br>'
                '<small style="color: #666;">Configure para recibir pagos</small>'
            )

    payment_status.short_description = "Estado de Pago"

    def get_queryset(self, request):
        """Filter hostels by role"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return qs

        if (
            hasattr(request.user, "is_shelter_admin")
            and request.user.is_shelter_admin()
        ):
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(id=request.user.shelter.id)

        return qs.none()

    def has_add_permission(self, request):
        """Only Super Admins can create hostels"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete hostels"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Super Admin and Shelter Admin can edit"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        if (
            hasattr(request.user, "is_shelter_admin")
            and request.user.is_shelter_admin()
        ):
            if obj is None:
                return True
            return obj == request.user.shelter
        return False

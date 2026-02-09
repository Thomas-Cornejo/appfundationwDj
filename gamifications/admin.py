from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    CareAction, CareIndicator, DirectPayment, Mission, Rank,
    UserMissionProgress, Wallet, WalletRecharge, WalletTransaction,
)


@admin.register(CareIndicator)
class CareIndicatorAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_display",
        "animal_display",
        "shelter_display",
        "food_badge",
        "hygiene_badge",
        "health_badge",
        "overall_badge",
        "needs_attention_icon",
        "has_health_events_icon",
        "created_at",
    ]

    list_filter = [
        "engagement__animal__shelter",
        "created_at",
    ]

    search_fields = [
        "engagement__user__username",
        "engagement__animal__name",
        "engagement__animal__shelter__name",
    ]

    readonly_fields = [
        "engagement",
        "created_at",
        "updated_at",
        "last_food_update",
        "last_hygiene_update",
        "last_health_update",
        "overall_status",
        "get_status_color",
    ]

    fieldsets = (
        ("Información del Apadrinamiento", {"fields": ("engagement",)}),
        (
            "Indicadores Actuales",
            {
                "fields": (
                    ("food_level", "last_food_update"),
                    ("hygiene_level", "last_hygiene_update"),
                    ("health_level", "last_health_update"),
                ),
                "description": "Niveles actuales de cada indicador (0-100%). Comida e higiene se degradan automáticamente. Salud solo baja con eventos médicos.",
            },
        ),
        (
            "Estado General",
            {
                "fields": ("overall_status", "get_status_color"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadatos",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["reset_indicators"]

    def has_add_permission(self, request):
        """Los indicadores se crean automáticamente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar indicadores"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def user_display(self, obj):
        """Muestra el usuario (padrino)"""
        try:
            return obj.user.username
        except Exception as e:
            return f"Error: {str(e)}"

    user_display.short_description = "Usuario"

    def animal_display(self, obj):
        """Muestra el animal"""
        try:
            return obj.animal.name
        except Exception as e:
            return f"Error: {str(e)}"

    animal_display.short_description = "Animal"

    def shelter_display(self, obj):
        """Muestra el albergue"""
        try:
            return obj.shelter.name
        except Exception as e:
            return f"Error: {str(e)}"

    shelter_display.short_description = "Albergue"

    def food_badge(self, obj):
        """Badge colorizado para nivel de comida"""
        try:
            return self._create_level_badge(obj.food_level, "🍖")
        except Exception as e:
            return f"Error: {str(e)}"

    food_badge.short_description = "Comida"

    def hygiene_badge(self, obj):
        """Badge colorizado para nivel de higiene"""
        try:
            return self._create_level_badge(obj.hygiene_level, "🧼")
        except Exception as e:
            return f"Error: {str(e)}"

    hygiene_badge.short_description = "Higiene"

    def health_badge(self, obj):
        """Badge colorizado para nivel de salud"""
        try:
            return self._create_level_badge(obj.health_level, "❤️")
        except Exception as e:
            return f"Error: {str(e)}"

    health_badge.short_description = "Salud"

    def overall_badge(self, obj):
        """Badge para estado general"""
        try:
            status = obj.overall_status
            color = self._get_color_by_level(status)
            return format_html(
                '<span style="background-color: {}; color: white; padding: 4px 12px; '
                'border-radius: 12px; font-weight: bold; font-size: 11px;">{}%</span>',
                color,
                status,
            )
        except Exception as e:
            return f"Error: {str(e)}"

    overall_badge.short_description = "Estado General"

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

    needs_attention_icon.short_description = "Alerta"

    def has_health_events_icon(self, obj):
        """Muestra si el animal tiene eventos de salud pendientes"""
        try:
            from animals.models import History

            pending_events = History.objects.filter(
                animal=obj.animal, status__in=["P", "T"], cost_coins__gt=0
            ).count()

            if pending_events > 0:
                return format_html(
                    '<span style="font-size: 18px;" title="{} evento(s) de salud activo(s)">🏥 {}</span>',
                    pending_events,
                    pending_events,
                )
            return format_html('<span style="color: green;">-</span>')
        except Exception as e:
            return f"Error: {str(e)}"

    has_health_events_icon.short_description = "🏥 Eventos"

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
                level,
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))

    def _get_color_by_level(self, level):
        """Retorna color según nivel"""
        try:
            level = int(level) if level is not None else 0
            if level >= 70:
                return "#10b981"
            elif level >= 40:
                return "#f59e0b"
            else:
                return "#ef4444"
        except:
            return "#6b7280"

    def reset_indicators(self, request, queryset):
        """Resetear todos los indicadores al 100%"""
        try:
            count = queryset.count()
            queryset.update(
                food_level=100,
                hygiene_level=100,
                health_level=100,
                last_food_update=timezone.now(),
                last_hygiene_update=timezone.now(),
                last_health_update=timezone.now(),
            )
            self.message_user(request, f"{count} indicador(es) reseteado(s) al 100%.")
        except Exception as e:
            self.message_user(request, f"Error al resetear: {str(e)}", level="error")

    reset_indicators.short_description = "Resetear al 100%"

    def get_queryset(self, request):
        """Filtrar por permisos usando Groups"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(engagement__animal__shelter=request.user.shelter)
            return qs.none()

        return qs.none()


@admin.register(CareAction)
class CareActionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "created_at",
        "user_display",
        "animal_display",
        "action_badge",
        "amount_increased",
        "coins_spent",
        "xp_earned",
    ]

    list_filter = [
        "action_type",
        "created_at",
        "care_indicator__engagement__animal__shelter",
    ]

    search_fields = [
        "care_indicator__engagement__user__username",
        "care_indicator__engagement__animal__name",
    ]

    readonly_fields = [
        "care_indicator",
        "action_type",
        "amount_increased",
        "coins_spent",
        "xp_earned",
        "created_at",
    ]

    fieldsets = (
        (
            "Información de la Acción",
            {"fields": ("care_indicator", "action_type", "created_at")},
        ),
        ("Detalles", {"fields": ("amount_increased", "coins_spent", "xp_earned")}),
    )

    def user_display(self, obj):
        """Usuario que realizó la acción"""
        return obj.user.username

    user_display.short_description = "Usuario"

    def animal_display(self, obj):
        """Animal que fue cuidado"""
        return obj.animal.name

    animal_display.short_description = "Animal"

    def action_badge(self, obj):
        """Badge colorizado según el tipo de acción"""
        colors = {
            "F": "#10b981",
            "H": "#3b82f6",
            "M": "#ef4444",
        }
        icons = {"F": "🍖", "H": "🧼", "M": "💊"}
        color = colors.get(obj.action_type, "#6b7280")
        icon = icons.get(obj.action_type, "❓")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{} {}</span>',
            color,
            icon,
            obj.get_action_type_display(),
        )

    action_badge.short_description = "Tipo"

    def has_add_permission(self, request):
        """Las acciones se crean desde la aplicación"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar acciones"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def get_queryset(self, request):
        """Filtrar por permisos usando Groups"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(care_indicator__engagement__animal__shelter=request.user.shelter)
            return qs.none()

        return qs.none()


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "shelter",
        "balance_display",
        "total_earned",
        "total_spent",
        "created_at",
    ]
    list_filter = ["shelter", "created_at"]
    search_fields = ["user__username", "shelter__name"]
    readonly_fields = [
        "user",
        "shelter",
        "balance",
        "total_earned",
        "total_spent",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Información de la Billetera",
            {"fields": ("user", "shelter")},
        ),
        (
            "Monedas",
            {
                "fields": (
                    "balance",
                    "total_earned",
                    "total_spent",
                )
            },
        ),
        (
            "Fechas",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def balance_display(self, obj):
        """Formato bonito para el balance"""
        return format_html(
            '<span style="background-color: #10b981; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-weight: bold;">🪙 {} monedas</span>',
            obj.balance,
        )

    balance_display.short_description = "Balance"

    def has_add_permission(self, request):
        """Las billeteras se crean automáticamente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar billeteras"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def get_queryset(self, request):
        """Filtrar billeteras por permisos usando Groups"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(shelter=request.user.shelter)
            return qs.none()

        return qs.none()


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "created_at",
        "user_display",
        "shelter_display",
        "transaction_badge",
        "amount_display",
        "description",
    ]

    list_filter = ["transaction_type", "created_at", "wallet__shelter"]

    search_fields = ["wallet__user__username", "description", "wallet__shelter__name"]

    readonly_fields = [
        "wallet",
        "transaction_type",
        "amount",
        "description",
        "created_at",
    ]

    fieldsets = (
        (
            "Transacción",
            {
                "fields": (
                    "wallet",
                    "transaction_type",
                    "amount",
                    "description",
                    "created_at",
                )
            },
        ),
    )

    def user_display(self, obj):
        """Usuario de la transacción"""
        return obj.wallet.user.username

    user_display.short_description = "Usuario"

    def shelter_display(self, obj):
        """Albergue de la transacción"""
        return obj.wallet.shelter.name if obj.wallet.shelter else "-"

    shelter_display.short_description = "Albergue"

    def transaction_badge(self, obj):
        """Badge según tipo de transacción"""
        if obj.transaction_type == "E":
            color = "#10b981"
            icon = "💰"
            text = "Ingreso"
        else:
            color = "#ef4444"
            icon = "💸"
            text = "Gasto"

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{} {}</span>',
            color,
            icon,
            text,
        )

    transaction_badge.short_description = "Tipo"

    def amount_display(self, obj):
        """Muestra el monto con signo"""
        symbol = "+" if obj.transaction_type == "E" else "-"
        color = "#10b981" if obj.transaction_type == "E" else "#ef4444"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{} 🪙</span>',
            color,
            symbol,
            obj.amount,
        )

    amount_display.short_description = "Monto"

    def has_add_permission(self, request):
        """Las transacciones se crean automáticamente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar transacciones"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def get_queryset(self, request):
        """Filtrar transacciones por permisos usando Groups"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(wallet__shelter=request.user.shelter)
            return qs.none()

        return qs.none()


@admin.register(WalletRecharge)
class WalletRechargeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "created_at",
        "user_display",
        "amount_cop",
        "coins_received",
        "payment_method",
        "status_badge",
        "shelter_display",
        "approve_button",
    ]

    list_filter = ["status", "payment_method", "created_at", "wallet__shelter"]

    search_fields = ["wallet__user__username", "transaction_id", "payment_reference", "wallet__shelter__name"]

    readonly_fields = [
        "wallet",
        "amount_cop",
        "coins_received",
        "created_at",
        "approved_at",
    ]

    fieldsets = (
        (
            "Información de la Recarga",
            {"fields": ("wallet", "amount_cop", "coins_received")},
        ),
        ("Pago", {"fields": ("payment_method", "transaction_id", "payment_reference")}),
        ("Estado", {"fields": ("status", "admin_notes")}),
        ("Fechas", {"fields": ("created_at", "approved_at"), "classes": ("collapse",)}),
    )

    actions = ["approve_recharges", "reject_recharges"]

    def has_add_permission(self, request):
        """Las recargas se crean desde la aplicación"""
        return False

    def user_display(self, obj):
        """Usuario que hizo la recarga"""
        return obj.wallet.user.username

    user_display.short_description = "Usuario"

    def shelter_display(self, obj):
        """Albergue donde se hizo la recarga"""
        return obj.wallet.shelter.name if obj.wallet.shelter else "-"

    shelter_display.short_description = "Albergue"

    def status_badge(self, obj):
        """Badge colorizado según estado"""
        colors = {
            "P": "#f59e0b",
            "A": "#10b981",
            "R": "#ef4444",
            "F": "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Estado"

    def approve_button(self, obj):
        """Botón para aprobación rápida"""
        if obj.status == "P":
            return format_html(
                '<a class="button" href="#" onclick="return false;" '
                'style="background-color: #10b981; color: white; padding: 5px 10px; '
                'border-radius: 5px; text-decoration: none;">Aprobar</a>'
            )
        return "-"

    approve_button.short_description = "Acción"

    def approve_recharges(self, request, queryset):
        """Aprobar recargas pendientes"""
        count = 0
        for recharge in queryset.filter(status="P"):
            if recharge.approve():
                count += 1

        self.message_user(request, f"{count} recarga(s) aprobada(s) exitosamente.")

    approve_recharges.short_description = "Aprobar recargas seleccionadas"

    def reject_recharges(self, request, queryset):
        """Rechazar recargas pendientes"""
        count = 0
        for recharge in queryset.filter(status="P"):
            if recharge.reject():
                count += 1

        self.message_user(request, f"{count} recarga(s) rechazada(s).")

    reject_recharges.short_description = "Rechazar recargas seleccionadas"

    def get_queryset(self, request):
        """Filtrar recargas por permisos usando Groups"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(wallet__shelter=request.user.shelter)
            return qs.none()

        return qs.none()


@admin.register(DirectPayment)
class DirectPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "animal",
        "shelter",
        "amount_cop_formatted",
        "status_badge",
        "created_at",
        "transfer_action",
    ]
    list_filter = ["status", "shelter", "created_at"]
    search_fields = [
        "user__username",
        "history__animal__name",
        "shelter__name",
        "transaction_id",
    ]
    readonly_fields = [
        "user",
        "history",
        "shelter",
        "amount_cop",
        "payment_reference",
        "transaction_id",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Información del Pago",
            {"fields": ("user", "history", "shelter", "amount_cop", "status")},
        ),
        (
            "Información de Transacción",
            {"fields": ("payment_reference", "transaction_id")},
        ),
        (
            "Transferencia al Albergue",
            {"fields": ("transferred_at", "transfer_reference", "admin_notes")},
        ),
        ("Fechas", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def amount_cop_formatted(self, obj):
        return f"${obj.amount_cop:,.2f} COP"

    amount_cop_formatted.short_description = "Monto"

    def animal(self, obj):
        return obj.history.animal.name if obj.history else "-"

    animal.short_description = "Animal"

    def status_badge(self, obj):
        colors = {"P": "#f59e0b", "A": "#10b981", "T": "#3b82f6", "R": "#ef4444"}
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Estado"

    def transfer_action(self, obj):
        """Botón para marcar como transferido"""
        if obj.status == "A":
            return format_html(
                '<a href="/admin/gamifications/directpayment/{}/mark-transferred/" '
                'style="background-color:#10b981; color:white; padding:6px 12px; '
                'border-radius:6px; text-decoration:none; font-size:11px;">✓ Marcar Transferido</a>',
                obj.id,
            )
        elif obj.status == "T":
            return format_html(
                '<span style="color:#10b981; font-weight:bold;">✓ Transferido</span>'
            )
        return "-"

    transfer_action.short_description = "Acción"

    def has_add_permission(self, request):
        """Los pagos directos se crean desde la aplicación"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar pagos"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def get_queryset(self, request):
        """Filtrar pagos directos por permisos usando Groups"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(shelter=request.user.shelter)
            return qs.none()

        return qs.none()


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ["order", "name", "min_xp", "icon", "color"]
    list_editable = ["name", "min_xp", "icon", "color"]
    ordering = ["order", "min_xp"]

    fieldsets = (
        (
            "Información del Rango",
            {
                "fields": (
                    "name",
                    "min_xp",
                    "icon",
                    "color",
                    "order",
                )
            },
        ),
    )

    def has_module_permission(self, request):
        """Solo Super Admin puede ver el módulo de Rangos"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """Solo Super Admin puede ver rangos"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_add_permission(self, request):
        """Solo Super Admin puede crear rangos"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Solo Super Admin puede editar rangos"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar rangos"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "order",
        "mission_type",
        "action_type",
        "target_count",
        "xp_reward",
        "coins_reward",
        "is_active",
    ]
    list_editable = ["is_active", "order"]
    list_filter = ["mission_type", "action_type", "is_active"]
    search_fields = ["title", "description"]
    ordering = ["order", "-created_at"]

    fieldsets = (
        (
            "Información de la Misión",
            {
                "fields": (
                    "title",
                    "description",
                    "mission_type",
                    "action_type",
                    "icon",
                    "order",
                    "is_active",
                )
            },
        ),
        (
            "Objetivos y Recompensas",
            {
                "fields": (
                    "target_count",
                    "xp_reward",
                    "coins_reward",
                )
            },
        ),
    )

    def has_module_permission(self, request):
        """Solo Super Admin puede ver el módulo de Misiones"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """Solo Super Admin puede ver misiones"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_add_permission(self, request):
        """Solo Super Admin puede crear misiones"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Solo Super Admin puede editar misiones"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar misiones"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False


@admin.register(UserMissionProgress)
class UserMissionProgressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "mission",
        "progress_display",
        "is_completed",
        "period_date",
        "completed_at",
    ]
    list_filter = [
        "is_completed",
        "mission__mission_type",
        "period_date",
    ]
    search_fields = ["user__username", "mission__title"]
    readonly_fields = ["created_at", "updated_at", "progress_percentage"]
    ordering = ["-created_at"]

    def progress_display(self, obj):
        return f"{obj.current_count}/{obj.mission.target_count} ({obj.progress_percentage}%)"

    progress_display.short_description = "Progreso"

    fieldsets = (
        (
            "Información del Progreso",
            {
                "fields": (
                    "user",
                    "mission",
                    "current_count",
                    "progress_percentage",
                    "is_completed",
                    "completed_at",
                )
            },
        ),
        (
            "Periodo",
            {"fields": ("period_date",)},
        ),
        (
            "Metadatos",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        """El progreso se crea automáticamente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar progreso"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    CareAction, CareIndicator, DirectPayment, Mission, Rank, ShelterWalletBalance,
    UserMissionProgress, VirtualWallet, WalletRecharge, WalletTransaction,
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

    def user_display(self, obj):
        """Shows the user (godfather)"""
        try:
            return obj.user.username
        except Exception as e:
            return f"Error: {str(e)}"

    user_display.short_description = "Usuario"

    def animal_display(self, obj):
        """Show the animal"""
        try:
            return obj.animal.name
        except Exception as e:
            return f"Error: {str(e)}"

    animal_display.short_description = "Animal"

    def shelter_display(self, obj):
        """Show the hostel"""
        try:
            return obj.shelter.name
        except Exception as e:
            return f"Error: {str(e)}"

    shelter_display.short_description = "Albergue"

    def food_badge(self, obj):
        """Colored badge for food level"""
        try:
            return self._create_level_badge(obj.food_level, "🍖")
        except Exception as e:
            return f"Error: {str(e)}"

    food_badge.short_description = "Comida"

    def hygiene_badge(self, obj):
        """Colored badge for hygiene level"""
        try:
            return self._create_level_badge(obj.hygiene_level, "🧼")
        except Exception as e:
            return f"Error: {str(e)}"

    hygiene_badge.short_description = "Higiene"

    def health_badge(self, obj):
        """Colored badge for health level"""
        try:
            return self._create_level_badge(obj.health_level, "❤️")
        except Exception as e:
            return f"Error: {str(e)}"

    health_badge.short_description = "Salud"

    def overall_badge(self, obj):
        """Badge for general status"""
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
        """Alert icon if you need attention"""
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
        """It shows if the animal has any pending health events."""
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
        """Create a color-coded badge according to the level"""
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
        """Returns color according to level"""
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
        """Reset all indicators to 100%"""
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
            self.message_user(request, f"{count} indicador(es) reseteado(s) al 100%%.")
        except Exception as e:
            self.message_user(request, f"Error al resetear: {str(e)}", level="error")

    reset_indicators.short_description = "Resetear al 100%%"

    def get_queryset(self, request):
        """Filter by permissions"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return qs

        if hasattr(request.user, "is_shelter_admin") and request.user.is_shelter_admin():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(engagement__animal__shelter=request.user.shelter)

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
        """User who performed the action"""
        return obj.user.username

    user_display.short_description = "Usuario"

    def animal_display(self, obj):
        """Animal that was cared for"""
        return obj.animal.name

    animal_display.short_description = "Animal"

    def action_badge(self, obj):
        """Badge color according to the type of action"""
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
        """No se pueden crear acciones manualmente desde el admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete actions"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        return False

    def get_queryset(self, request):
        """Filter by permissions"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return qs

        if hasattr(request.user, "is_shelter_admin") and request.user.is_shelter_admin():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(care_indicator__engagement__animal__shelter=request.user.shelter)

        return qs.none()


@admin.register(VirtualWallet)
class VirtualWalletAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "balance_display",
        "total_earned",
        "total_spent",
        "created_at",
    ]

    list_filter = ["created_at"]
    search_fields = ["user__username", "user__email"]

    readonly_fields = [
        "user",
        "balance",
        "total_earned",
        "total_spent",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Usuario", {"fields": ("user",)}),
        ("Saldo Actual", {"fields": ("balance",)}),
        ("Estadísticas", {"fields": ("total_earned", "total_spent")}),
        (
            "Metadatos",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def balance_display(self, obj):
        """Show off your balance in style"""
        color = "#10b981" if obj.balance > 0 else "#ef4444"
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">🪙 {} monedas</span>',
            color,
            obj.balance,
        )

    balance_display.short_description = "Saldo"

    def has_add_permission(self, request):
        """Wallets cannot be created manually"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete wallets"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        return False


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "created_at",
        "user_display",
        "transaction_badge",
        "amount_display",
        "description",
    ]

    list_filter = ["transaction_type", "created_at"]

    search_fields = ["wallet__user__username", "description"]

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
        """Transaction user"""
        return obj.wallet.user.username

    user_display.short_description = "Usuario"

    def transaction_badge(self, obj):
        """Badge according to transaction type"""
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
        """Show the signed amount"""
        symbol = "+" if obj.transaction_type == "E" else "-"
        color = "#10b981" if obj.transaction_type == "E" else "#ef4444"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color,
            symbol,
            obj.amount,
        )

    amount_display.short_description = "Monto"

    def has_add_permission(self, request):
        """Transactions cannot be created manually"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Super Admin can delete transactions"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return True
        return False


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
        "shelter",
        "approve_button",
    ]

    list_filter = ["status", "payment_method", "shelter", "created_at"]

    search_fields = ["wallet__user__username", "transaction_id", "payment_reference"]

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
            {"fields": ("wallet", "amount_cop", "coins_received", "shelter")},
        ),
        ("Pago", {"fields": ("payment_method", "transaction_id", "payment_reference")}),
        ("Estado", {"fields": ("status", "admin_notes")}),
        ("Fechas", {"fields": ("created_at", "approved_at"), "classes": ("collapse",)}),
    )

    actions = ["approve_recharges", "reject_recharges"]

    def user_display(self, obj):
        """User who made the recharge"""
        return obj.wallet.user.username

    user_display.short_description = "Usuario"

    def status_badge(self, obj):
        """Badge color according to state"""
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
        """Button for quick approval"""
        if obj.status == "P":
            return format_html(
                '<a class="button" href="#" onclick="return false;" '
                'style="background-color: #10b981; color: white; padding: 5px 10px; '
                'border-radius: 5px; text-decoration: none;">Aprobar</a>'
            )
        return "-"

    approve_button.short_description = "Acción"

    def approve_recharges(self, request, queryset):
        """Approve pending recharges"""
        count = 0
        for recharge in queryset.filter(status="P"):
            if recharge.approve():
                count += 1

        self.message_user(request, f"{count} recarga(s) aprobada(s) exitosamente.")

    approve_recharges.short_description = "Aprobar recargas seleccionadas"

    def reject_recharges(self, request, queryset):
        """Approve pending recharges"""
        count = 0
        for recharge in queryset.filter(status="P"):
            if recharge.reject():
                count += 1

        self.message_user(request, f"{count} recarga(s) rechazada(s).")

    reject_recharges.short_description = "Rechazar recargas seleccionadas"

    def get_queryset(self, request):
        """Filter by permissions"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "is_superadmin") and request.user.is_superadmin():
            return qs

        if hasattr(request.user, "is_shelter_admin") and request.user.is_shelter_admin():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(shelter=request.user.shelter)

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
        return f"${obj.amount_cop:,.2f}"

    amount_cop_formatted.short_description = "Monto"

    def animal(self, obj):
        return obj.history.animal.name

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
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ShelterWalletBalance)
class ShelterWalletBalanceAdmin(admin.ModelAdmin):
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
            "Información del Balance",
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
            'border-radius: 12px; font-weight: bold;">{} monedas</span>',
            obj.balance,
        )

    balance_display.short_description = "Balance"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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

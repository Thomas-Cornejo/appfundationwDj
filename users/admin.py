# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from shelters.models import Shelter

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "shelter_display",
        "groups_display",
        "is_staff",
        "is_active",
        "date_joined",
    ]

    list_filter = [
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
        "shelter",
        "date_joined",
    ]

    search_fields = ["username", "email", "first_name", "last_name"]

    fieldsets = UserAdmin.fieldsets + (
        ("Información Adicional", {"fields": ("address", "phone", "shelter")}),
        (
            "Gamificación",
            {
                "fields": ("experience_points",),
                "classes": ("collapse",),
                "description": "Puntos ganados por interacciones en el sistema de apadrinamiento",
            },
        ),
        (
            "Metadatos",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Información Adicional",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "address",
                    "phone",
                    "shelter",
                    "groups",
                )
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at"]

    def shelter_display(self, obj):
        """Muestra el albergue con formato"""
        if obj.shelter:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 2px 8px; '
                'border-radius: 6px; font-size: 11px;">{}</span>',
                obj.shelter.name
            )
        return format_html('<span style="color: #9ca3af;">Sin albergue</span>')

    shelter_display.short_description = "Albergue"

    def groups_display(self, obj):
        """Muestra los grupos del usuario con badges"""
        groups = obj.groups.all()
        if groups:
            colors = {
                "Super Admin": "#ef4444",
                "Shelter Admin": "#f59e0b",
                "Regular User": "#10b981",
            }
            badges = []
            for group in groups:
                color = colors.get(group.name, "#6b7280")
                badges.append(
                    f'<span style="background-color: {color}; color: white; padding: 2px 8px; '
                    f'border-radius: 6px; font-size: 11px; margin-right: 4px;">{group.name}</span>'
                )
            return format_html("".join(badges))
        return format_html('<span style="color: #9ca3af;">Sin grupo</span>')

    groups_display.short_description = "Grupos"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Personalizar campos ForeignKey en el formulario.
        Restringir albergues visibles según el rol.
        """
        if db_field.name == "shelter":
            if request.user.is_superuser:
                kwargs["queryset"] = Shelter.objects.all()
            elif request.user.groups.filter(name="Super Admin").exists():
                kwargs["queryset"] = Shelter.objects.all()
            elif request.user.groups.filter(name="Shelter Admin").exists():
                if hasattr(request.user, "shelter") and request.user.shelter:
                    kwargs["queryset"] = Shelter.objects.filter(id=request.user.shelter.id)
                else:
                    kwargs["queryset"] = Shelter.objects.none()
            else:
                kwargs["queryset"] = Shelter.objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Restringir grupos que pueden ser asignados según el rol del admin.
        """
        if db_field.name == "groups":
            from django.contrib.auth.models import Group
            
            if request.user.is_superuser:
                kwargs["queryset"] = Group.objects.all()
            elif request.user.groups.filter(name="Super Admin").exists():
                kwargs["queryset"] = Group.objects.all()
            elif request.user.groups.filter(name="Shelter Admin").exists():
                kwargs["queryset"] = Group.objects.filter(name="Regular User")
            else:
                kwargs["queryset"] = Group.objects.none()

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        """
        Filtrar usuarios según permisos usando Groups.
        Super Admin ve todos, Shelter Admin solo usuarios de su albergue.
        """
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="Super Admin").exists():
            return qs

        if request.user.groups.filter(name="Shelter Admin").exists():
            if hasattr(request.user, "shelter") and request.user.shelter:
                from django.db.models import Q
                return qs.filter(
                    Q(shelter=request.user.shelter) |
                    Q(shelter__isnull=True, groups__name="Regular User")
                ).distinct()
            return qs.none()

        return qs.none()

    def has_add_permission(self, request):
        """Super Admin y Shelter Admin pueden crear usuarios"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name__in=["Super Admin", "Shelter Admin"]).exists():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Admin puede eliminar usuarios"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Super Admin y Shelter Admin pueden editar usuarios"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="Super Admin").exists():
            return True

        if request.user.groups.filter(name="Shelter Admin").exists():
            if obj is None:  
                return True
            if hasattr(request.user, "shelter") and request.user.shelter:
                if obj.shelter == request.user.shelter:
                    return True
                if obj.shelter is None and obj.groups.filter(name="Regular User").exists():
                    return True
            return False

        return False

    def save_model(self, request, obj, form, change):
        """
        Auto-asignar el shelter del Shelter Admin al crear usuarios.
        """
        if not change:
            if request.user.groups.filter(name="Shelter Admin").exists():
                if hasattr(request.user, "shelter") and request.user.shelter:
                    if not obj.shelter:
                        obj.shelter = request.user.shelter
        
        super().save_model(request, obj, form, change)
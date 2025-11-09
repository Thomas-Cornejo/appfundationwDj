# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from shelters.models import Shelter

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "shelter",
        "get_groups",
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

    def get_groups(self, obj):
        """Displays user groups"""
        groups = obj.groups.all()
        if groups:
            return ", ".join([g.name for g in groups])
        return "Sin grupo"

    get_groups.short_description = "Grupos"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customize the ForeignKey fields in the admin form.
        Restrict visible shelters based on user role.
        """
        if db_field.name == "shelter":
            if request.user.is_superuser:
                kwargs["queryset"] = Shelter.objects.all()
            elif hasattr(request.user, "shelter") and request.user.shelter:
                kwargs["queryset"] = Shelter.objects.filter(id=request.user.shelter.id)
            else:
                kwargs["queryset"] = Shelter.objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        """
        Filter users based on permissions. Super Admin sees everyone,
        Shelter Admin only sees users in their shelter.
        """
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "is_shelter_admin") and request.user.is_shelter_admin():
            if hasattr(request.user, "shelter") and request.user.shelter:
                return qs.filter(shelter=request.user.shelter)

        return qs

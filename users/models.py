from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from shelters.models import Shelter


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    address = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Dirección de domicilio"
    )
    phone = PhoneNumberField(
        region="CO", blank=False, null=False, default="0000000000", verbose_name="Teléfono"
    )
    shelter = models.ForeignKey(
        Shelter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_members",
        verbose_name="Albergue asignado",
        help_text="Solo para Shelter Admins: albergue que gestionan",
    )
    experience_points = models.PositiveIntegerField(default=0, verbose_name="Puntos de experiencia")
    coins = models.PositiveIntegerField(default=0, verbose_name="Monedas virtuales")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username} ({self.get_user_role()})"

    # ==================== ROLES ====================

    def get_user_role(self):
        """Retorna el rol principal del usuario"""
        if self.is_superadmin():
            return "Super Admin"
        elif self.is_shelter_admin():
            return "Shelter Admin"
        elif self.is_regular_user():
            return "Usuario Regular"
        return "Sin rol"

    def is_superadmin(self):
        """Verifica si es super administrador (acceso total)"""
        return self.is_superuser or self.groups.filter(name="Super Admin").exists()

    def is_shelter_admin(self):
        """Verifica si es administrador de albergue (gestión de un albergue)"""
        return self.groups.filter(name="Shelter Admin").exists()

    def is_regular_user(self):
        """
        Verifica si es usuario regular (puede adoptar/apadrinar)
        Por defecto, cualquier usuario sin grupo asignado es regular
        """
        return self.groups.filter(name="Regular User").exists() or not self.groups.exists()

    # ==================== PERMISOS ====================

    def can_manage_shelter(self, shelter):
        """Verifica si puede gestionar un albergue específico"""
        if self.is_superadmin():
            return True  # Super Admin puede gestionar todos los albergues
        if self.is_shelter_admin() and self.shelter == shelter:
            return True  # Shelter Admin solo su albergue asignado
        return False

    def can_manage_all_shelters(self):
        """Verifica si puede gestionar todos los albergues"""
        return self.is_superadmin()

    def can_approve_engagements(self):
        """Verifica si puede aprobar/rechazar solicitudes"""
        return self.is_superadmin() or self.is_shelter_admin()

    def can_manage_animals(self, animal=None):
        """Verifica si puede gestionar animales"""
        if self.is_superadmin():
            return True
        if self.is_shelter_admin():
            if animal:
                return animal.shelter == self.shelter
            return True  # Puede gestionar animales de su albergue
        return False

    def can_access_admin(self):
        """Verifica si tiene acceso al panel de administración"""
        return self.is_superadmin() or self.is_shelter_admin() or self.is_staff

    def can_adopt_or_sponsor(self):
        """Verifica si puede adoptar o apadrinar animales"""
        return self.is_regular_user() or not (self.is_superadmin() or self.is_shelter_admin())

    # ==================== SHELTER MANAGEMENT ====================

    def get_managed_shelter(self):
        """Retorna el albergue que gestiona (si es shelter admin)"""
        if self.is_shelter_admin():
            return self.shelter
        return None

    def get_accessible_shelters(self):
        """Retorna los albergues a los que tiene acceso"""
        if self.is_superadmin():
            return Shelter.objects.all()
        elif self.is_shelter_admin() and self.shelter:
            return Shelter.objects.filter(id=self.shelter.id)
        return Shelter.objects.none()

    # ==================== GAMIFICATION ====================

    def get_rank(self):
        """Obtiene el rango actual del usuario basado en XP"""
        from gamifications.models import Rank

        return Rank.objects.filter(min_xp__lte=self.experience_points).order_by("-min_xp").first()

    def add_xp(self, amount):
        """Agrega experiencia al usuario"""
        if amount > 0:
            self.experience_points += amount
            self.save(update_fields=["experience_points"])
        return self.experience_points

    def add_coins(self, amount):
        """Agrega monedas virtuales al usuario"""
        if amount > 0:
            self.coins += amount
            self.save(update_fields=["coins"])
        return self.coins

    def spend_coins(self, amount):
        """Gasta monedas virtuales (retorna True si tiene suficientes)"""
        if amount > 0 and self.coins >= amount:
            self.coins -= amount
            self.save(update_fields=["coins"])
            return True
        return False

    def get_xp_progress(self):
        """Retorna el progreso hacia el siguiente rango"""
        current_rank = self.get_rank()
        if not current_rank:
            return {"current": 0, "next": 100, "percentage": 0}

        from gamifications.models import Rank

        next_rank = Rank.objects.filter(min_xp__gt=current_rank.min_xp).order_by("min_xp").first()

        if not next_rank:
            return {
                "current": self.experience_points,
                "next": current_rank.min_xp,
                "percentage": 100,
                "is_max_rank": True,
            }

        current_xp_in_range = self.experience_points - current_rank.min_xp
        total_xp_needed = next_rank.min_xp - current_rank.min_xp
        percentage = int((current_xp_in_range / total_xp_needed) * 100)

        return {
            "current": self.experience_points,
            "next": next_rank.min_xp,
            "percentage": percentage,
            "current_rank": current_rank,
            "next_rank": next_rank,
            "is_max_rank": False,
        }

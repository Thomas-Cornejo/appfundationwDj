from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from shelters.models import Shelter


class CustomUser(AbstractUser):
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
    )
    experience_points = models.SmallIntegerField(default=0, verbose_name="Puntos de experiencia")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username}"

    def is_superadmin(self):
        """Check if they are a super administrator"""
        return self.is_superuser or self.groups.filter(name="Super Admin").exists()

    def is_shelter_admin(self):
        """Check if they are a hostel manager"""
        return self.groups.filter(name="Shelter Admin").exists()

    def is_regular_user(self):
        """Check if they are a regular user (they can adopt/sponsor)"""
        return self.groups.filter(name="Regular User").exists() or not self.groups.exists()

    def can_manage_shelter(self, shelter):
        """Check if you can manage a specific hostel"""
        if self.is_superadmin():
            return True
        if self.is_shelter_admin() and self.shelter == shelter:
            return True
        return False

    def get_managed_shelter(self):
        """Return the shelter you manage (if you are shelter admin)"""
        if self.is_shelter_admin():
            return self.shelter
        return None

    def get_rank(self):
        """Obtiene el rango actual del usuario basado en XP"""
        from gamifications.models import Rank

        return Rank.objects.filter(min_xp__lte=self.experience_points).order_by("-min_xp").first()

    def add_xp(self, amount):
        """Agrega experiencia al usuario"""
        self.experience_points += amount
        self.save()
        return self.experience_points

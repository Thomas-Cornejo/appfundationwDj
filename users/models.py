from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("VOLUNTARIO", "Voluntario"),
        ("ADMIN", "Admin"),
        ("PADRINO_ADOPTANTE", "Padrino-Adoptante"),
    ]

    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="PADRINO_ADOPTANTE", 
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

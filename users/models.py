from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):

    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

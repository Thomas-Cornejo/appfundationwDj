from django.conf import settings
from django.db import models

from animals.models import Animal

ENGAGEMENTS_TYPES_CHOICES = [
    ("A", "Adoption"), ("S", "Sponsorship"), ("D", "Donate")]

STATUS_CHOICES = [
    ("P", "Pending"),
    ("A", "Approved"),
    ("R", "Rejected"),
]


class AnimalEngagement(models.Model):
    engagements_type = models.CharField(
        max_length=1, choices=ENGAGEMENTS_TYPES_CHOICES)
    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default="P")
    pdf_file = models.FileField(
        upload_to="adoptions_pdfs/", blank=True, null=True)
    form_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    animal = models.ForeignKey(
        Animal, on_delete=models.CASCADE, related_name="engagements"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="engagements"
    )
    admin_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Animal Engagement"
        verbose_name_plural = "Animal Engagements"

    def __str__(self):
        return f"#{self.id} - {self.user.username} - {self.get_engagements_type_display()} - {self.animal.name}"

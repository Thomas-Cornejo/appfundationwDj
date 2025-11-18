from django.conf import settings
from django.db import models

from animals.models import Animal

ENGAGEMENTS_TYPES_CHOICES = [("A", "Adoption"), ("S", "Sponsorship"), ("D", "Donate")]

STATUS_CHOICES = [
    ("P", "Pending"),
    ("A", "Approved"),
    ("R", "Rejected"),
]


class AnimalEngagement(models.Model):
    engagements_type = models.CharField(max_length=1, choices=ENGAGEMENTS_TYPES_CHOICES)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="P")
    pdf_file = models.FileField(upload_to="adoptions_pdfs/", blank=True, null=True)
    form_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="engagements")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="engagements"
    )
    admin_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Gestión de Adopcion - Apadrinamiento"
        verbose_name_plural = "Gestión de Adopciones - Apadrinamientos"

    def __str__(self):
        return f"#{self.id} - {self.user.username} - {self.get_engagements_type_display()} - {self.animal.name}"


class Visit(models.Model):
    """
    Modelo para registrar visitas programadas a animales adoptados.
    El administrador puede programar visitas y evaluar el estado del animal.
    """

    EVALUATION_CHOICES = [
        (1, "Muy Mala"),
        (2, "Mala"),
        (3, "Regular"),
        (4, "Buena"),
        (5, "Excelente"),
    ]

    animal_engagement = models.ForeignKey(
        AnimalEngagement,
        on_delete=models.CASCADE,
        related_name="visits",
        limit_choices_to={"status": "A", "engagements_type": "A"},  # Solo adopciones aprobadas
        help_text="Adopción a la que pertenece esta visita",
    )
    visit_date = models.DateTimeField(help_text="Fecha y hora programada para la visita")
    notes = models.TextField(blank=True, null=True, help_text="Notas u observaciones de la visita")
    evaluation = models.IntegerField(
        choices=EVALUATION_CHOICES,
        blank=True,
        null=True,
        help_text="Evaluación del estado del animal (1-5). Se completa después de la visita.",
    )
    completed = models.BooleanField(default=False, help_text="Indica si la visita ya fue realizada")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-visit_date"]
        verbose_name = "Visita"
        verbose_name_plural = "Visitas"

    def __str__(self):
        status = "Realizada" if self.completed else "Programada"
        return f"Visita {status} - {self.animal_engagement.animal.name} - {self.visit_date.strftime('%d/%m/%Y')}"

    @property
    def is_pending(self):
        """Retorna True si la visita está pendiente (no completada y fecha futura)"""
        from django.utils import timezone

        return not self.completed and self.visit_date > timezone.now()

    @property
    def user(self):
        """Acceso directo al usuario adoptante"""
        return self.animal_engagement.user

    @property
    def animal(self):
        """Acceso directo al animal"""
        return self.animal_engagement.animal

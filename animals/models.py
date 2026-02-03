from datetime import date

from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from breeds.models import Breed
from shelters.models import Shelter

SEX_CHOICES = [("M", "Macho"), ("H", "Hembra")]
SIZE_CHOICES = [("G", "Grande"), ("M", "Mediano"), ("P", "Pequeño")]
AVAILABILITY_CHOICES = [("A", "Adopcion"), ("S", "Apadrinamiento"), ("B", "Ambos")]
STATUS_CHOICES = [("O", "Huerfano"), ("S", "Apadrinado"), ("A", "Adoptado")]


class Animal(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    birth_date = models.DateField(verbose_name="Fecha de nacimiento aprox.")
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, verbose_name="Sexo")
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, verbose_name="Tamaño")
    color = models.CharField(max_length=20, verbose_name="Color")
    imagen = CloudinaryField("image")
    availability = models.CharField(
        max_length=1,
        choices=AVAILABILITY_CHOICES,
        default="A",
        verbose_name="Disponibilidad",
    )
    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default="O", verbose_name="Estado del animal"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, verbose_name="Raza")
    shelter = models.ForeignKey(
        Shelter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="animals",
        verbose_name="Albergue",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Animalito"
        verbose_name_plural = "Animalitos"

    def __str__(self):
        return f"{self.name} ({self.breed})"

    @property
    def age(self):
        """Return the animal's age in years."""
        today = date.today()
        age = (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )
        return age

    def ingreso_history(self):
        return self.history.filter(history_type="I").first()


HISTORY_TYPE_CHOICES = [
    ("V", "Vacunación"),
    ("E", "Esterilización"),
    ("C", "Cirugía"),
    ("T", "Tratamiento"),
    ("U", "Urgencia"),
    ("I", "Ingreso"),
    ("O", "Otro"),
]

HISTORY_STATUS_CHOICES = [
    ("P", "Pendiente"),
    ("T", "En tratamiento"),
    ("C", "Completado"),
]


class History(models.Model):
    history_type = models.CharField(
        max_length=1,
        choices=HISTORY_TYPE_CHOICES,
        default="I",
        verbose_name="Tipo de historia",
    )
    description = models.TextField(verbose_name="Descripción")
    location_found = models.CharField(
        max_length=255,
        verbose_name="Dónde se encontró",
        blank=True,
        null=True,
        help_text="Solo llenar si es un ingreso. Dejar vacío para eventos médicos.",
    )

    clinical_document = CloudinaryField(
        blank=True,
        null=True,
        resource_type="auto",
        folder="clinical_histories",
        verbose_name="Documento clínico",
        help_text="Sube la historia clínica en formato PDF, JPG, JPEG, PNG o WEBP",
    )

    entry_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de historia")
    exit_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de salida")
    status = models.CharField(
        max_length=1,
        choices=HISTORY_STATUS_CHOICES,
        default="C",
        verbose_name="Estado",
    )

    health_impact = models.IntegerField(
        default=0,
        verbose_name="Impacto en salud (%)",
    )

    cost_coins = models.IntegerField(
        default=0,
        verbose_name="Costo en monedas virtuales",
    )

    contributed_coins = models.IntegerField(
        default=0,
        verbose_name="Monedas contribuidas",
    )

    is_urgent = models.BooleanField(
        default=False,
        verbose_name="¿Es urgente?",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    animal = models.ForeignKey(
        Animal,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Animal",
        related_name="history",
    )

    class Meta:
        verbose_name = "Historia"
        verbose_name_plural = "Historias"
        ordering = ["-entry_date"]

    def __str__(self):
        return f"{self.get_history_type_display()} - {self.animal.name if self.animal else 'Sin animal'}"


def clean(self):
    """Validar formato de archivo clínico"""
    super().clean()

    if self.clinical_document:
        try:
            file_url = str(self.clinical_document.url)
            extension = file_url.split(".")[-1].lower().split("?")[0]

            allowed_formats = ["pdf", "jpg", "jpeg", "png", "webp"]

            if extension not in allowed_formats:
                raise ValidationError(
                    {
                        "clinical_document": f'Formato no permitido. Solo se aceptan: {", ".join(allowed_formats).upper()}'
                    }
                )
        except ValidationError:
            raise
        except AttributeError:
            pass
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error al validar documento clínico: {e}")

    @property
    def is_health_event(self):
        """Verifica si es un evento de salud que requiere contribución"""
        return self.history_type in ["V", "C", "T", "U"] and self.cost_coins > 0

    @property
    def needs_contribution(self):
        """Verifica si necesita contribuciones actualmente"""
        return self.status == "P" and self.cost_coins > 0

    @property
    def progress_percentage(self):
        """Porcentaje de progreso en contribuciones (0-100)"""
        if self.cost_coins == 0:
            return 100
        return min(100, int((self.contributed_coins / self.cost_coins) * 100))

    @property
    def remaining_coins(self):
        """Monedas que faltan para completar el tratamiento"""
        return max(0, self.cost_coins - self.contributed_coins)

    @property
    def is_fully_funded(self):
        """Verifica si ya se completó el financiamiento"""
        return self.contributed_coins >= self.cost_coins

    def apply_health_impact(self):
        """
        Aplica el impacto negativo en la salud del animal.
        Solo funciona si el animal tiene un CareIndicator activo.
        """
        if self.health_impact > 0 and self.animal:
            try:
                from engagements.models import AnimalEngagement

                engagement = AnimalEngagement.objects.filter(
                    animal=self.animal, engagements_type="S", status="A"
                ).first()

                if engagement and hasattr(engagement, "care_indicator"):
                    indicator = engagement.care_indicator
                    indicator.health_level = max(0, indicator.health_level - self.health_impact)
                    indicator.last_health_update = timezone.now()
                    indicator.save()
                    return True
                else:
                    print(f"Animal {self.animal.name} no tiene CareIndicator activo")
                    return False
            except Exception as e:
                print(f"Error aplicando impacto de salud: {e}")
                return False
        return False

    def resolve_event(self):
        """
        Resuelve el evento y restaura la salud del animal.
        Se llama cuando el tratamiento está completamente financiado.
        """
        self.status = "C"
        self.exit_date = timezone.now()
        self.save()

        if self.health_impact > 0 and self.animal:
            try:
                from engagements.models import AnimalEngagement

                engagement = AnimalEngagement.objects.filter(
                    animal=self.animal, engagements_type="S", status="A"
                ).first()

                if engagement and hasattr(engagement, "care_indicator"):
                    indicator = engagement.care_indicator
                    indicator.health_level = min(100, indicator.health_level + self.health_impact)
                    indicator.last_health_update = timezone.now()
                    indicator.save()
                    return True
            except Exception as e:
                print(f"Error resolviendo evento: {e}")
                return False
        return False

    def contribute(self, coins):
        """
        Registra una contribución de monedas al tratamiento.
        Si se completa el financiamiento, resuelve automáticamente el evento.
        """
        if coins <= 0:
            return False

        self.contributed_coins += coins
        if self.is_fully_funded:
            self.resolve_event()
        else:
            if self.status == "P":
                self.status = "T"

        self.save()
        return True

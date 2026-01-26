from django.core.management.base import BaseCommand
from engagements.models import AnimalEngagement
from gamifications.models import CareIndicator


class Command(BaseCommand):
    help = 'Crea CareIndicators faltantes para apadrinamientos aprobados'

    def handle(self, *args, **options):
        # Encuentra apadrinamientos aprobados
        sponsorships = AnimalEngagement.objects.filter(
            engagements_type='S',
            status='A'
        )

        total = sponsorships.count()
        self.stdout.write(f'📊 Total apadrinamientos aprobados: {total}')

        created_indicators = 0

        for eng in sponsorships:
            # Crear CareIndicator si no existe
            ci, ci_created = CareIndicator.objects.get_or_create(
                engagement=eng,
                defaults={
                    'food_level': 100,
                    'hygiene_level': 100,
                    'health_level': 100
                }
            )
            if ci_created:
                created_indicators += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ CareIndicator: {eng.user.username} → {eng.animal.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ CareIndicators creados: {created_indicators}/{total}'
            )
        )
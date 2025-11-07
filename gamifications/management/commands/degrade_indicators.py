from django.core.management.base import BaseCommand
from django.utils import timezone
from gamifications.models import CareIndicator

class Command(BaseCommand):
    help = 'Degrada automáticamente los indicadores de cuidado'

    def handle(self, *args, **options):
        indicators = CareIndicator.objects.select_related(
            'engagement__animal__shelter'
        ).filter(
            engagement__status='A',
            engagement__animal__is_active=True
        )
        
        degraded_count = 0
        total_count = indicators.count()
        
        for indicator in indicators:
            try:
                if indicator.apply_degradation():
                    degraded_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error en indicador {indicator.id}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Completado: {degraded_count}/{total_count} indicadores degradados'
            )
        )
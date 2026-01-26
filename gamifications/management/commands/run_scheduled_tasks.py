from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone


class Command(BaseCommand):
    help = 'Ejecuta tareas programadas según la hora actual (UTC)'

    def handle(self, *args, **options):
        now = timezone.now()
        hora_utc = now.hour
        minuto = now.minute
        
        self.stdout.write(
            self.style.WARNING(f'\n{"="*60}')
        )
        self.stdout.write(
            self.style.WARNING(f'Verificación de tareas programadas')
        )
        self.stdout.write(
            self.style.WARNING(f'Hora actual (UTC): {now.strftime("%Y-%m-%d %H:%M:%S")}')
        )
        self.stdout.write(
            self.style.WARNING(f'{"="*60}\n')
        )

        tareas_ejecutadas = False
        if minuto == 0 and hora_utc % 4 == 0:
            self.stdout.write(
                self.style.SUCCESS(f'Ejecutando: degrade_indicators')
            )
            try:
                call_command('degrade_indicators')
                self.stdout.write(
                    self.style.SUCCESS('degrade_indicators completado exitosamente\n')
                )
                tareas_ejecutadas = True
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error en degrade_indicators: {e}\n')
                )
        
        if hora_utc == 10 and minuto == 1:
            self.stdout.write(
                self.style.SUCCESS(f'Ejecutando: reset_missions')
            )
            try:
                call_command('reset_missions')
                self.stdout.write(
                    self.style.SUCCESS('reset_missions completado exitosamente\n')
                )
                tareas_ejecutadas = True
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error en reset_missions: {e}\n')
                )
        
        if not tareas_ejecutadas:
            self.stdout.write(
                self.style.WARNING('No hay tareas programadas para esta hora')
            )
            self.stdout.write(
                self.style.WARNING(f'Próximas ejecuciones:')
            )
            
            proxima_degradacion = ((hora_utc // 4) + 1) * 4
            if proxima_degradacion >= 24:
                proxima_degradacion = 0
            self.stdout.write(
                self.style.WARNING(f'  • degrade_indicators: {proxima_degradacion:02d}:00 UTC')
            )
            
            if hora_utc < 10 or (hora_utc == 10 and minuto < 1):
                self.stdout.write(
                    self.style.WARNING(f'  • reset_missions: 10:01 UTC (hoy)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  • reset_missions: 10:01 UTC (mañana)')
                )
        
        self.stdout.write(
            self.style.WARNING(f'\n{"="*60}\n')
        )
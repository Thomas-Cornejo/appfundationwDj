"""
Management command para calcular y ejecutar la distribución SEMANAL de fondos a albergues.
Ejecuta pagos cada semana para que las fundaciones reciban el dinero más rápido.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from gamifications.models import CoinUsage, MonthlyDistribution
from shelters.models import Shelter
import requests
from django.conf import settings


class Command(BaseCommand):
    help = 'Calcula y ejecuta distribución SEMANAL a albergues usando Wompi Payouts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Ejecutar pagos reales (por defecto solo muestra reporte)',
        )
        parser.add_argument(
            '--week',
            type=str,
            help='Semana a procesar (formato: YYYY-MM-DD del lunes, default: semana anterior)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular ejecución sin hacer pagos reales',
        )

    def handle(self, *args, **options):
        execute = options['execute']
        dry_run = options['dry_run']
        
        if options['week']:
            week_start = datetime.strptime(options['week'], '%Y-%m-%d').date()
        else:
            today = timezone.now().date()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            week_start = last_monday
        
        week_end = week_start + timedelta(days=7)
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS(
            f"  DISTRIBUCIÓN SEMANAL - Semana del {week_start} al {week_end}"
        ))
        self.stdout.write("=" * 80)
        
        usage_by_shelter = CoinUsage.objects.filter(
            created_at__gte=week_start,
            created_at__lt=week_end
        ).values('shelter').annotate(
            total_coins=Sum('coins_used'),
            total_cop=Sum('amount_cop')
        )
        
        if not usage_by_shelter:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  No hay usos de monedas en esta semana"
            ))
            return
        
        distributions = []
        total_amount = 0
        
        self.stdout.write("\n" + "-" * 80)
        self.stdout.write("CÁLCULO DE DISTRIBUCIÓN:")
        self.stdout.write("-" * 80)
        
        for usage in usage_by_shelter:
            shelter = Shelter.objects.get(id=usage['shelter'])
            coins = usage['total_coins']
            amount = float(usage['total_cop'])
            
            self.stdout.write(f"\n📍 {shelter.name}")
            self.stdout.write(f"   Monedas usadas: {coins:,}")
            self.stdout.write(f"   Monto: ${amount:,.2f} COP")
            self.stdout.write(f"   Método de pago: {shelter.get_payment_method_display()}")
            
            if not shelter.has_payment_info():
                self.stdout.write(self.style.WARNING(
                    f"   ⚠️  ALERTA: No tiene información de pago configurada"
                ))
            else:
                self.stdout.write(f"   Pagar a: {shelter.get_payment_info_display()}")
            
            distribution, created = MonthlyDistribution.objects.get_or_create(
                shelter=shelter,
                month=week_start,
                defaults={
                    'total_coins_used': coins,
                    'amount_cop': amount,
                    'status': 'P'
                }
            )
            
            if not created:
                distribution.total_coins_used = coins
                distribution.amount_cop = amount
                distribution.status = 'P'
                distribution.save()
            
            distributions.append(distribution)
            total_amount += amount
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS(
            f"TOTAL A DISTRIBUIR ESTA SEMANA: ${total_amount:,.2f} COP"
        ))
        self.stdout.write("=" * 80)
        
        if not execute:
            self.stdout.write("\n" + self.style.WARNING(
                "💡 Esto es solo un reporte. Para ejecutar pagos usa: --execute"
            ))
            self.stdout.write(self.style.WARNING(
                "💡 Para simulación sin pagos reales usa: --execute --dry-run"
            ))
            return
        
        self.stdout.write("\n" + "=" * 80)
        if dry_run:
            self.stdout.write(self.style.WARNING("🧪 MODO DRY-RUN - NO SE HARÁN PAGOS REALES"))
        else:
            self.stdout.write(self.style.SUCCESS("🚀 EJECUTANDO PAGOS SEMANALES..."))
        self.stdout.write("=" * 80)
        
        success_count = 0
        failed_count = 0
        
        for distribution in distributions:
            shelter = distribution.shelter
            
            self.stdout.write(f"\nProcesando: {shelter.name} - ${distribution.amount_cop:,.2f}")
            
            if not shelter.has_payment_info():
                self.stdout.write(self.style.ERROR(
                    f"   ✗ ERROR: {shelter.name} no tiene información de pago configurada"
                ))
                distribution.mark_as_failed("No tiene información de pago configurada")
                failed_count += 1
                continue
            
            try:
                if dry_run:
                    result = {
                        'success': True,
                        'payout_id': f'DRY_RUN_WEEK_{timezone.now().timestamp()}'
                    }
                    self.stdout.write(self.style.WARNING(
                        f"   ⚠️  DRY-RUN: Se habría enviado ${distribution.amount_cop:,.2f} a {shelter.get_payment_info_display()}"
                    ))
                else:
                    result = self.execute_payout(distribution, week_start)
                
                if result['success']:
                    distribution.mark_as_paid(result['payout_id'])
                    success_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"   ✓ ÉXITO: Payout ID: {result['payout_id']}"
                    ))
                else:
                    distribution.mark_as_failed(result['error'])
                    failed_count += 1
                    
                    self.stdout.write(self.style.ERROR(
                        f"   ✗ ERROR: {result['error']}"
                    ))
            
            except Exception as e:
                error_msg = str(e)
                distribution.mark_as_failed(error_msg)
                failed_count += 1
                
                self.stdout.write(self.style.ERROR(
                    f"   ✗ EXCEPCIÓN: {error_msg}"
                ))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("RESUMEN DE EJECUCIÓN:"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"✓ Exitosos: {success_count}")
        self.stdout.write(f"✗ Fallidos: {failed_count}")
        self.stdout.write(f"Total procesados: {len(distributions)}")
        self.stdout.write("=" * 80)
        self.stdout.write("\n💡 TIP: Configura un cron job para ejecutar esto cada lunes:")
        self.stdout.write("   0 9 * * 1 cd /path/to/project && python manage.py weekly_payout --execute")
    
    def execute_payout(self, distribution, week_start):
        """Ejecuta un pago usando Wompi Payouts API"""
        shelter = distribution.shelter
        
        if shelter.payment_method == 'NEQUI':
            if not shelter.nequi_phone:
                return {'success': False, 'error': 'Número Nequi no configurado'}
            
            recipient = {
                'type': 'NEQUI',
                'phone_number': shelter.nequi_phone,
                'full_name': shelter.legal_name or shelter.name
            }
        
        elif shelter.payment_method == 'BANK':
            if not shelter.bank_account_number or not shelter.bank_name:
                return {'success': False, 'error': 'Datos bancarios incompletos'}
            
            recipient = {
                'type': 'BANK_ACCOUNT',
                'bank_code': self.get_bank_code(shelter.bank_name),
                'account_number': shelter.bank_account_number,
                'account_type': shelter.bank_account_type or 'SAVINGS',
                'full_name': shelter.legal_name or shelter.name,
                'legal_id': shelter.identification_number or '000000000',
                'legal_id_type': 'CC'
            }
        
        else:
            return {'success': False, 'error': 'Método de pago no soportado para Payouts'}
        
        url = 'https://production.wompi.co/v1/payouts'
        headers = {
            'Authorization': f'Bearer {settings.WOMPI_PRIVATE_KEY}',
            'Content-Type': 'application/json'
        }
        
        week_number = week_start.isocalendar()[1] 
        
        data = {
            'amount_in_cents': int(distribution.amount_cop * 100),
            'currency': 'COP',
            'customer_email': shelter.email,
            'payment_method': recipient,
            'reference': f"WEEK_{shelter.id}_W{week_number}_{week_start.year}",
            'payment_description': f"Distribución semanal - Semana {week_number} {week_start.year}"
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'payout_id': result.get('data', {}).get('id', 'N/A')
                }
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('reason', f'HTTP {response.status_code}')
                return {
                    'success': False,
                    'error': error_msg
                }
        
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Timeout en la petición'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Error de conexión: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Error inesperado: {str(e)}'}
    
    def get_bank_code(self, bank_name):
        """Mapeo de nombres de banco a códigos Wompi"""
        bank_codes = {
            'Bancolombia': '1007',
            'Banco de Bogotá': '1001',
            'Davivienda': '1051',
            'BBVA Colombia': '1013',
            'Banco Popular': '1002',
            'Banco de Occidente': '1023',
            'Banco AV Villas': '1052',
            'Banco Caja Social': '1032',
            'Banco Agrario': '1040',
            'Citibank': '1009',
            'Banco GNB Sudameris': '1012',
            'HSBC Colombia': '1062',
            'Scotiabank Colpatria': '1019',
            'Itaú': '1006',
            'Banco Falabella': '1062',
            'Banco Pichincha': '1060',
            'Banco Cooperativo Coopcentral': '1066',
            'Banco Serfinanza': '1069',
        }
        return bank_codes.get(bank_name, '1007')

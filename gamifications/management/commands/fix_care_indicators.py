from django.core.management.base import BaseCommand

from engagements.models import AnimalEngagement
from gamifications.models import CareIndicator, Wallet


class Command(BaseCommand):
    help = "Crea CareIndicators y Wallets faltantes para apadrinamientos aprobados"

    def handle(self, *args, **options):
        # Encuentra apadrinamientos aprobados
        sponsorships = AnimalEngagement.objects.filter(engagements_type="S", status="A")

        total = sponsorships.count()
        self.stdout.write(f"📊 Total apadrinamientos aprobados: {total}")

        created_indicators = 0
        created_wallets = 0

        for eng in sponsorships:
            # Crear CareIndicator si no existe
            ci, ci_created = CareIndicator.objects.get_or_create(
                engagement=eng,
                defaults={"food_level": 100, "hygiene_level": 100, "health_level": 100},
            )
            if ci_created:
                created_indicators += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ CareIndicator: {eng.user.username} → {eng.animal.name}")
                )

            # Crear Wallet si no existe
            wallet, wallet_created = Wallet.objects.get_or_create(
                user=eng.user,
                shelter=eng.animal.shelter,
                defaults={
                    "balance": 0,
                    "total_earned": 0,
                    "total_spent": 0,
                },
            )
            if wallet_created:
                created_wallets += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Wallet: {eng.user.username} en {eng.animal.shelter.name}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Resumen:\n"
                f"   CareIndicators creados: {created_indicators}\n"
                f"   Wallets creadas: {created_wallets}\n"
                f"   Total procesados: {total}"
            )
        )

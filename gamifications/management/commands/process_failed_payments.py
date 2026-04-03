from django.core.management.base import BaseCommand

from gamifications.models import PaymentEvent, WalletRecharge
from gamifications.services.idempotency import generate_idempotency_key

MAX_RETRIES = 3

NON_RETRYABLE_REASONS = {
    "INSUFFICIENT_FUNDS",
    "PAYMENT_METHOD_DECLINED",
    "CARD_NOT_AUTHORIZED",
    "INVALID_CARD",
    "SUSPECTED_FRAUD",
    "USER_CANCELLED",
    "EXPIRED_CARD",
}


class Command(BaseCommand):
    help = "Evalúa pagos fallidos y registra eventos RETRYING para los elegibles."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        failed_events = PaymentEvent.get_failed_retryable()

        self.stdout.write(f"Pagos con último estado FAILED: {failed_events.count()}\n")
        self.stdout.write("-" * 60)

        for event in failed_events:
            recharge = event.recharge

            retry_count = recharge.events.filter(status__in=["RETRYING", "APPROVED"]).count()

            self.stdout.write(
                f"\nRecarga #{recharge.id} | "
                f"{recharge.wallet.user.username} | "
                f"${recharge.amount_cop:,.0f} | "
                f"Razón: {event.failure_reason or 'sin detalle'} | "
                f"Intentos: {retry_count}/{MAX_RETRIES}"
            )

            is_retryable, reason = self._evaluate(event, retry_count)

            if not is_retryable:
                self.stdout.write(self.style.ERROR(f"  {reason}"))

                if retry_count >= MAX_RETRIES and not dry_run:
                    idempotency_key = generate_idempotency_key(
                        wallet_id=recharge.wallet.id,
                        shelter_id=recharge.wallet.shelter.id,
                        amount_cop=int(recharge.amount_cop),
                        username=recharge.wallet.user.username,
                    )
                    if not recharge.events.filter(status="ABANDONED").exists():
                        PaymentEvent.objects.create(
                            recharge=recharge,
                            status="ABANDONED",
                            idempotency_key=f"abandoned:{idempotency_key}",
                            failure_reason=reason,
                        )
                continue

            idempotency_key = generate_idempotency_key(
                wallet_id=recharge.wallet.id,
                shelter_id=recharge.wallet.shelter.id,
                amount_cop=int(recharge.amount_cop),
                username=recharge.wallet.user.username,
            )

            if PaymentEvent.objects.filter(idempotency_key=idempotency_key).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Ya existe un evento con esta key hoy — idempotente, se omite"
                    )
                )
                continue

            self.stdout.write(
                self.style.SUCCESS(
                    f"  Elegible → registrando RETRYING | key: {idempotency_key[:16]}..."
                )
            )

            if not dry_run:
                PaymentEvent.objects.create(
                    recharge=recharge,
                    status="RETRYING",
                    idempotency_key=idempotency_key,
                    failure_reason=event.failure_reason,
                    metadata={
                        "evaluated_at": str(
                            __import__(
                                "django.utils.timezone", fromlist=["timezone"]
                            ).timezone.now()
                        )
                    },
                )

        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: sin cambios en BD."))

    def _evaluate(self, event: PaymentEvent, retry_count: int) -> tuple[bool, str]:
        if retry_count >= MAX_RETRIES:
            return False, f"Límite de {MAX_RETRIES} reintentos alcanzado"

        if event.recharge.events.filter(status="APPROVED").exists():
            return False, "Ya existe un evento aprobado para esta recarga"

        reason_upper = (event.failure_reason or "").upper()
        for non_retryable in NON_RETRYABLE_REASONS:
            if non_retryable in reason_upper:
                return False, f"Rechazo definitivo: {event.failure_reason}"

        return True, "Error transitorio, elegible para reintento"

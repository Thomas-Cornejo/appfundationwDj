"""
Resetea las misiones diarias y semanales según corresponda.
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from gamifications.models import Mission, UserMissionProgress

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Resetea las misiones diarias y semanales según corresponda"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula el reseteo sin aplicar cambios en la base de datos",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())

        logger.info(
            "Inicio de reseteo de misiones | fecha=%s | dry_run=%s",
            today,
            dry_run,
        )

        daily_deleted = self._reset_daily_missions(today, dry_run)
        weekly_deleted = self._reset_weekly_missions(start_of_week, dry_run)

        total_deleted = daily_deleted + weekly_deleted

        if dry_run:
            logger.warning(
                "[DRY RUN] Se resetearían %s progresos diarios y %s semanales (total=%s)",
                daily_deleted,
                weekly_deleted,
                total_deleted,
            )
        else:
            if total_deleted > 0:
                logger.info(
                    "Reseteo completado | diarios=%s | semanales=%s | total=%s",
                    daily_deleted,
                    weekly_deleted,
                    total_deleted,
                )
            else:
                logger.info("Reseteo completado | no se encontraron progresos antiguos")

    def _reset_daily_missions(self, today, dry_run):
        daily_missions = Mission.objects.filter(
            mission_type="daily",
            is_active=True,
        )

        deleted_count = 0

        for mission in daily_missions:
            old_progress = UserMissionProgress.objects.filter(
                mission=mission,
                period_date__lt=today,
            )

            count = old_progress.count()
            if count == 0:
                continue

            logger.debug(
                "Misión diaria '%s' | progresos antiguos=%s",
                mission.title,
                count,
            )

            if not dry_run:
                deleted, _ = old_progress.delete()
                deleted_count += deleted
            else:
                deleted_count += count

        return deleted_count

    def _reset_weekly_missions(self, start_of_week, dry_run):
        weekly_missions = Mission.objects.filter(
            mission_type="weekly",
            is_active=True,
        )

        deleted_count = 0

        for mission in weekly_missions:
            old_progress = UserMissionProgress.objects.filter(
                mission=mission,
                period_date__lt=start_of_week,
            )

            count = old_progress.count()
            if count == 0:
                continue

            logger.debug(
                "Misión semanal '%s' | progresos antiguos=%s",
                mission.title,
                count,
            )

            if not dry_run:
                deleted, _ = old_progress.delete()
                deleted_count += deleted
            else:
                deleted_count += count

        return deleted_count

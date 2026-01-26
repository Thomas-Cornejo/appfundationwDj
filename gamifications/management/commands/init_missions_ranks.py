"""
Management command para inicializar misiones y rangos por defecto.
"""

import logging

from django.core.management.base import BaseCommand

from gamifications.models import Mission, Rank

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Inicializa rangos y misiones por defecto del sistema de gamificación"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula la inicialización sin escribir en la base de datos",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        logger.info("Inicializando sistema de gamificación | dry_run=%s", dry_run)

        ranks_created = self._init_ranks(dry_run)
        daily_created = self._init_missions(self._daily_missions(), "daily", dry_run)
        weekly_created = self._init_missions(self._weekly_missions(), "weekly", dry_run)
        achievement_created = self._init_missions(
            self._achievement_missions(), "achievement", dry_run
        )

        total_created = ranks_created + daily_created + weekly_created + achievement_created

        if dry_run:
            logger.warning(
                "[DRY RUN] Se crearían %s registros (rangos y misiones)",
                total_created,
            )
        else:
            logger.info(
                "Inicialización completada | rangos=%s | diarias=%s | semanales=%s | logros=%s",
                ranks_created,
                daily_created,
                weekly_created,
                achievement_created,
            )

    def _init_ranks(self, dry_run):
        ranks_data = [
            {"name": "Novato", "min_xp": 0, "icon": "🔰", "color": "gray", "order": 1},
            {"name": "Aprendiz", "min_xp": 100, "icon": "🐣", "color": "blue", "order": 2},
            {"name": "Cuidador", "min_xp": 300, "icon": "🐾", "color": "green", "order": 3},
            {"name": "Protector", "min_xp": 600, "icon": "🛡️", "color": "teal", "order": 4},
            {"name": "Guardian", "min_xp": 1000, "icon": "⭐", "color": "indigo", "order": 5},
            {"name": "Héroe Animal", "min_xp": 1500, "icon": "💎", "color": "purple", "order": 6},
            {"name": "Leyenda", "min_xp": 2500, "icon": "👑", "color": "gold", "order": 7},
        ]

        created_count = 0

        for data in ranks_data:
            if dry_run:
                exists = Rank.objects.filter(name=data["name"]).exists()
                if not exists:
                    created_count += 1
                continue

            _, created = Rank.objects.get_or_create(name=data["name"], defaults=data)
            if created:
                logger.debug("Rango creado: %s", data["name"])
                created_count += 1

        return created_count

    def _init_missions(self, missions_data, mission_type, dry_run):
        created_count = 0

        for data in missions_data:
            if dry_run:
                exists = Mission.objects.filter(
                    title=data["title"], mission_type=mission_type
                ).exists()
                if not exists:
                    created_count += 1
                continue

            _, created = Mission.objects.get_or_create(
                title=data["title"],
                mission_type=mission_type,
                defaults=data,
            )
            if created:
                logger.debug("Misión creada [%s]: %s", mission_type, data["title"])
                created_count += 1

        return created_count

    def _daily_missions(self):
        return [
            {
                "title": "Alimenta a tu mascota",
                "description": "Dale comida a tu animal apadrinado",
                "mission_type": "daily",
                "action_type": "feed",
                "target_count": 1,
                "xp_reward": 10,
                "coins_reward": 20,
                "icon": "🍖",
                "scope": "shelter",
                "order": 1,
            },
            {
                "title": "Mantén la higiene",
                "description": "Limpia a tu animal apadrinado",
                "mission_type": "daily",
                "action_type": "clean",
                "target_count": 1,
                "xp_reward": 10,
                "coins_reward": 20,
                "icon": "🧼",
                "scope": "shelter",
                "order": 2,
            },
            {
                "title": "Cuidador dedicado",
                "description": "Alimenta a tu mascota 3 veces en un día",
                "mission_type": "daily",
                "action_type": "feed",
                "target_count": 3,
                "xp_reward": 30,
                "coins_reward": 50,
                "icon": "🌟",
                "scope": "shelter",
                "order": 3,
            },
        ]

    def _weekly_missions(self):
        return [
            {
                "title": "Cuidador semanal",
                "description": "Alimenta a tu mascota 10 veces en la semana",
                "mission_type": "weekly",
                "action_type": "feed",
                "target_count": 10,
                "xp_reward": 100,
                "coins_reward": 150,
                "icon": "🏆",
                "scope": "shelter",
                "order": 1,
            },
            {
                "title": "Limpieza profunda",
                "description": "Limpia a tu mascota 7 veces en la semana",
                "mission_type": "weekly",
                "action_type": "clean",
                "target_count": 7,
                "xp_reward": 80,
                "coins_reward": 120,
                "icon": "✨",
                "scope": "shelter",
                "order": 2,
            },
            {
                "title": "Héroe de la salud",
                "description": "Contribuye a 3 tratamientos médicos",
                "mission_type": "weekly",
                "action_type": "health",
                "target_count": 3,
                "xp_reward": 150,
                "coins_reward": 200,
                "icon": "💚",
                "scope": "shelter",
                "order": 3,
            },
        ]

    def _achievement_missions(self):
        return [
            {
                "title": "Primer apadrinamiento",
                "description": "Apadrina tu primer animal",
                "mission_type": "achievement",
                "action_type": "sponsor",
                "target_count": 1,
                "xp_reward": 50,
                "coins_reward": 100,
                "icon": "🎉",
                "scope": "global",
                "order": 1,
            },
            {
                "title": "Padrino generoso",
                "description": "Apadrina 3 animales",
                "mission_type": "achievement",
                "action_type": "sponsor",
                "target_count": 3,
                "xp_reward": 200,
                "coins_reward": 500,
                "icon": "💖",
                "scope": "global",
                "order": 2,
            },
            {
                "title": "Ángel guardián",
                "description": "Apadrina 5 animales",
                "mission_type": "achievement",
                "action_type": "sponsor",
                "target_count": 5,
                "xp_reward": 500,
                "coins_reward": 1000,
                "icon": "😇",
                "scope": "global",
                "order": 3,
            },
        ]

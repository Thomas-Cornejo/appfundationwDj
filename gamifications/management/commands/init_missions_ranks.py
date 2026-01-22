"""
Management command para inicializar misiones y rangos por defecto.
"""
from django.core.management.base import BaseCommand

from gamifications.models import Mission, Rank


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Inicializando Sistema de Misiones y Rangos ==="))

        self.stdout.write("\n📊 Creando rangos...")
        ranks_data = [
            {"name": "Novato", "min_xp": 0, "icon": "🔰", "color": "gray", "order": 1},
            {"name": "Aprendiz", "min_xp": 100, "icon": "🐣", "color": "blue", "order": 2},
            {"name": "Cuidador", "min_xp": 300, "icon": "🐾", "color": "green", "order": 3},
            {"name": "Protector", "min_xp": 600, "icon": "🛡️", "color": "teal", "order": 4},
            {"name": "Guardian", "min_xp": 1000, "icon": "⭐", "color": "indigo", "order": 5},
            {"name": "Héroe Animal", "min_xp": 1500, "icon": "💎", "color": "purple", "order": 6},
            {"name": "Leyenda", "min_xp": 2500, "icon": "👑", "color": "gold", "order": 7},
        ]

        for rank_data in ranks_data:
            rank, created = Rank.objects.get_or_create(name=rank_data["name"], defaults=rank_data)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Creado: {rank_data['icon']} {rank_data['name']} ({rank_data['min_xp']} XP)"
                    )
                )
            else:
                self.stdout.write(f"  - Ya existe: {rank_data['name']}")

        self.stdout.write("\nCreando misiones diarias...")
        daily_missions = [
            {
                "title": "Alimenta a tu mascota",
                "description": "Dale comida a tu animal apadrinado",
                "mission_type": "daily",
                "action_type": "feed",
                "target_count": 1,
                "xp_reward": 10,
                "coins_reward": 20,
                "icon": "🍖",
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
                "order": 3,
            },
        ]

        for mission_data in daily_missions:
            mission, created = Mission.objects.get_or_create(
                title=mission_data["title"],
                mission_type="daily",
                defaults=mission_data,
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Creada: {mission_data['icon']} {mission_data['title']}"
                    )
                )
            else:
                self.stdout.write(f"  - Ya existe: {mission_data['title']}")

        self.stdout.write("\nCreando misiones semanales...")
        weekly_missions = [
            {
                "title": "Cuidador semanal",
                "description": "Alimenta a tu mascota 10 veces en la semana",
                "mission_type": "weekly",
                "action_type": "feed",
                "target_count": 10,
                "xp_reward": 100,
                "coins_reward": 150,
                "icon": "🏆",
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
                "order": 3,
            },
        ]

        for mission_data in weekly_missions:
            mission, created = Mission.objects.get_or_create(
                title=mission_data["title"],
                mission_type="weekly",
                defaults=mission_data,
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Creada: {mission_data['icon']} {mission_data['title']}"
                    )
                )
            else:
                self.stdout.write(f"  - Ya existe: {mission_data['title']}")

        self.stdout.write("\n🏅 Creando logros...")
        achievement_missions = [
            {
                "title": "Primer apadrinamiento",
                "description": "Apadrina tu primer animal",
                "mission_type": "achievement",
                "action_type": "sponsor",
                "target_count": 1,
                "xp_reward": 50,
                "coins_reward": 100,
                "icon": "🎉",
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
                "order": 2,
            },
        ]

        for mission_data in achievement_missions:
            mission, created = Mission.objects.get_or_create(
                title=mission_data["title"],
                mission_type="achievement",
                defaults=mission_data,
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Creado: {mission_data['icon']} {mission_data['title']}"
                    )
                )
            else:
                self.stdout.write(f"  - Ya existe: {mission_data['title']}")

        self.stdout.write(
            self.style.SUCCESS("\nSistema de Misiones y Rangos inicializado correctamente")
        )

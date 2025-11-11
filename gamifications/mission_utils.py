"""
Utilidades para el sistema de misiones.
"""
from datetime import date, timedelta

from django.db.models import Q

from gamifications.models import Mission, Rank, UserMissionProgress


def get_user_rank(user):
    """
    Obtiene el rango actual del usuario basado en su XP.
    """
    user_xp = user.experience_points
    rank = Rank.objects.filter(min_xp__lte=user_xp).order_by("-min_xp").first()
    return rank


def get_next_rank(user):
    """
    Obtiene el próximo rango que puede alcanzar el usuario.
    """
    user_xp = user.experience_points
    next_rank = Rank.objects.filter(min_xp__gt=user_xp).order_by("min_xp").first()
    return next_rank


def get_user_level_info(user):
    """
    Retorna información completa del nivel del usuario.
    Incluye: nivel actual, XP actual, XP para siguiente nivel, progreso.
    """
    current_rank = get_user_rank(user)
    next_rank = get_next_rank(user)

    user_xp = user.experience_points

    if current_rank is None:
        level = 1
        current_xp_in_level = user_xp
        xp_for_next_level = 100
    else:
        level = current_rank.order + 1
        current_xp_in_level = user_xp - current_rank.min_xp

        if next_rank:
            xp_for_next_level = next_rank.min_xp - current_rank.min_xp
        else:
            xp_for_next_level = 1
            current_xp_in_level = 1

    progress_percentage = min(100, int((current_xp_in_level / xp_for_next_level) * 100))

    return {
        "level": level,
        "current_rank": current_rank,
        "next_rank": next_rank,
        "user_xp": user_xp,
        "current_xp_in_level": current_xp_in_level,
        "xp_for_next_level": xp_for_next_level,
        "progress_percentage": progress_percentage,
    }


def get_or_create_mission_progress(user, mission, period_date=None):
    """
    Obtiene o crea el progreso de una misión para un usuario en un período específico.
    """
    if period_date is None:
        if mission.mission_type == "daily":
            period_date = date.today()
        elif mission.mission_type == "weekly":
            today = date.today()
            period_date = today - timedelta(days=today.weekday())
        else:
            period_date = date(2000, 1, 1)

    progress, created = UserMissionProgress.objects.get_or_create(
        user=user, mission=mission, period_date=period_date
    )

    return progress


def track_mission_progress(user, action_type, amount=1):
    """
    Rastrea el progreso del usuario en misiones relacionadas con una acción específica.

    Args:
        user: El usuario que realiza la acción
        action_type: Tipo de acción ('feed', 'clean', 'health', 'login', 'sponsor')
        amount: Cantidad de veces que se realizó la acción (default: 1)

    Returns:
        List[Mission]: Lista de misiones completadas durante esta acción
    """
    completed_missions = []

    missions = Mission.objects.filter(action_type=action_type, is_active=True)

    for mission in missions:
        progress = get_or_create_mission_progress(user, mission)

        if progress.is_completed:
            continue

        mission_completed = progress.increment_progress(amount)

        if mission_completed:
            completed_missions.append(mission)

    return completed_missions


def get_active_missions_for_user(user):
    """
    Obtiene todas las misiones activas con su progreso para un usuario.
    Retorna misiones diarias, semanales y logros no completados.
    """
    missions_data = []

    active_missions = Mission.objects.filter(is_active=True)

    for mission in active_missions:
        progress = get_or_create_mission_progress(user, mission)

        if mission.mission_type in ["daily", "weekly"]:
            pass

        missions_data.append(
            {
                "mission": mission,
                "progress": progress,
                "percentage": progress.progress_percentage,
                "is_completed": progress.is_completed,
            }
        )

    return missions_data


def reset_daily_missions(user):
    """
    Resetea las misiones diarias del usuario (para ser llamado al inicio del día).
    """
    today = date.today()

    UserMissionProgress.objects.filter(
        user=user,
        mission__mission_type="daily",
        mission__is_active=True,
        period_date__lt=today,
    ).update(is_completed=False, current_count=0)


def reset_weekly_missions(user):
    """
    Resetea las misiones semanales del usuario (para ser llamado al inicio de la semana).
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    UserMissionProgress.objects.filter(
        user=user,
        mission__mission_type="weekly",
        mission__is_active=True,
        period_date__lt=week_start,
    ).update(is_completed=False, current_count=0)

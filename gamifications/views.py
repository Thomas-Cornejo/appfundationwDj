import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from animals.models import History
from engagements.models import AnimalEngagement

from .mission_utils import get_active_missions_for_user, get_user_level_info, track_mission_progress
from .models import CareAction, CareIndicator, Wallet


def _get_wallet(user, shelter):
    """Helper function to get or create wallet for user and shelter."""
    wallet, _ = Wallet.objects.get_or_create(user=user, shelter=shelter, defaults={"balance": 0})
    return wallet


def _format_completed_missions(missions):
    """Helper function to format completed missions info."""
    return [{"title": m.title, "xp": m.xp_reward, "coins": m.coins_reward} for m in missions]


@login_required
def gamification_dashboard(request, animal_id):
    """
    Main view of gamification for a sponsored animal.
    It displays indicators and allows users to perform care actions.
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator, _ = CareIndicator.objects.get_or_create(
        engagement=engagement,
        defaults={"food_level": 100, "hygiene_level": 100, "health_level": 100},
    )

    shelter = engagement.animal.shelter
    wallet = _get_wallet(request.user, shelter)

    food_cost = int(shelter.food_unit_cost / 10)
    hygiene_cost = int(shelter.hygiene_unit_cost / 10)

    health_events = History.objects.filter(
        animal=engagement.animal, status__in=["P", "T"], cost_coins__gt=0
    ).order_by("-is_urgent", "entry_date")

    level_info = get_user_level_info(request.user)
    active_missions = get_active_missions_for_user(request.user)

    recent_actions = CareAction.objects.filter(care_indicator=care_indicator).order_by(
        "-created_at"
    )[:10]

    context = {
        "engagement": engagement,
        "animal": engagement.animal,
        "care_indicator": care_indicator,
        "wallet": wallet,
        "shelter": shelter,
        "food_cost": food_cost,
        "hygiene_cost": hygiene_cost,
        "health_events": health_events,
        "level_info": level_info,
        "active_missions": active_missions,
        "recent_actions": recent_actions,
    }

    return render(request, "gamifications/dashboard.html", context)


@login_required
@require_POST
def feed_animal(request, animal_id):
    """
    Action: Feed the animal.
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator = engagement.care_indicator
    shelter = engagement.animal.shelter
    wallet = _get_wallet(request.user, shelter)

    food_cost = int(shelter.food_unit_cost / 10)

    if not wallet.can_afford(food_cost):
        return JsonResponse(
            {"success": False, "error": "No tienes suficientes monedas"}, status=400
        )

    if care_indicator.food_level >= 100:
        return JsonResponse(
            {"success": False, "error": "El nivel de alimento ya está al máximo"},
            status=400,
        )

    increase = 10
    old_level = care_indicator.food_level
    care_indicator.food_level = min(100, care_indicator.food_level + increase)
    care_indicator.last_food_update = timezone.now()
    care_indicator.save()

    wallet.spend_coins(food_cost, f"Alimentar a {engagement.animal.name}")

    xp_earned = 10
    CareAction.objects.create(
        care_indicator=care_indicator,
        action_type="F",
        amount_increased=increase,
        coins_spent=food_cost,
        xp_earned=xp_earned,
    )

    completed_missions = track_mission_progress(request.user, "feed")
    missions_completed_info = _format_completed_missions(completed_missions)

    return JsonResponse(
        {
            "success": True,
            "new_level": care_indicator.food_level,
            "old_level": old_level,
            "coins_spent": food_cost,
            "new_balance": wallet.balance,
            "xp_earned": xp_earned,
            "message": f"¡{engagement.animal.name} ha comido! +{increase}% alimento",
            "missions_completed": missions_completed_info,
        }
    )


@login_required
@require_POST
def clean_animal(request, animal_id):
    """
    Action: Cleaning/hygiene of the animal.
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator = engagement.care_indicator
    shelter = engagement.animal.shelter
    wallet = _get_wallet(request.user, shelter)

    hygiene_cost = int(shelter.hygiene_unit_cost / 10)

    if not wallet.can_afford(hygiene_cost):
        return JsonResponse(
            {"success": False, "error": "No tienes suficientes monedas"}, status=400
        )

    if care_indicator.hygiene_level >= 100:
        return JsonResponse(
            {"success": False, "error": "El nivel de higiene ya está al máximo"},
            status=400,
        )

    increase = 10
    old_level = care_indicator.hygiene_level
    care_indicator.hygiene_level = min(100, care_indicator.hygiene_level + increase)
    care_indicator.last_hygiene_update = timezone.now()
    care_indicator.save()

    wallet.spend_coins(hygiene_cost, f"Limpiar a {engagement.animal.name}")

    xp_earned = 10
    CareAction.objects.create(
        care_indicator=care_indicator,
        action_type="H",
        amount_increased=increase,
        coins_spent=hygiene_cost,
        xp_earned=xp_earned,
    )

    completed_missions = track_mission_progress(request.user, "clean")
    missions_completed_info = _format_completed_missions(completed_missions)

    return JsonResponse(
        {
            "success": True,
            "new_level": care_indicator.hygiene_level,
            "old_level": old_level,
            "coins_spent": hygiene_cost,
            "new_balance": wallet.balance,
            "xp_earned": xp_earned,
            "message": f"¡{engagement.animal.name} está limpio! +{increase}% higiene",
            "missions_completed": missions_completed_info,
        }
    )


@login_required
@require_POST
def contribute_health(request, animal_id, history_id):
    """
    Action: Contribute coins to a health event.
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator = engagement.care_indicator
    shelter = engagement.animal.shelter
    wallet = _get_wallet(request.user, shelter)

    health_event = get_object_or_404(
        History, id=history_id, animal=engagement.animal, status__in=["P", "T"]
    )

    try:
        data = json.loads(request.body)
        contribution = int(data.get("amount", 0))
    except:
        contribution = int(request.POST.get("amount", 0))

    if contribution <= 0:
        return JsonResponse({"success": False, "error": "Cantidad inválida"}, status=400)

    remaining = health_event.remaining_coins
    if contribution > remaining:
        contribution = remaining

    if not wallet.can_afford(contribution):
        return JsonResponse(
            {"success": False, "error": "No tienes suficientes monedas"}, status=400
        )

    wallet.spend_coins(contribution, f"Tratamiento médico para {engagement.animal.name}")

    health_event.contribute(contribution)

    xp_earned = contribution // 2
    CareAction.objects.create(
        care_indicator=care_indicator,
        action_type="M",
        amount_increased=0,
        coins_spent=contribution,
        xp_earned=xp_earned,
    )

    completed_missions = track_mission_progress(request.user, "health")
    missions_completed_info = _format_completed_missions(completed_missions)

    return JsonResponse(
        {
            "success": True,
            "contribution": contribution,
            "new_balance": wallet.balance,
            "xp_earned": xp_earned,
            "progress": health_event.progress_percentage,
            "remaining": health_event.remaining_coins,
            "fully_funded": health_event.is_fully_funded,
            "message": f"Contribución exitosa: {contribution} monedas",
            "missions_completed": missions_completed_info,
        }
    )


@login_required
def get_care_status(request, animal_id):
    """
    API to obtain the current status of the indicators (for real-time updates).
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator = engagement.care_indicator
    shelter = engagement.animal.shelter
    wallet = _get_wallet(request.user, shelter)

    return JsonResponse(
        {
            "food_level": care_indicator.food_level,
            "hygiene_level": care_indicator.hygiene_level,
            "health_level": care_indicator.health_level,
            "overall_status": care_indicator.overall_status,
            "needs_attention": care_indicator.needs_attention(),
            "wallet_balance": wallet.balance,
            "status_color": care_indicator.get_status_color(),
        }
    )

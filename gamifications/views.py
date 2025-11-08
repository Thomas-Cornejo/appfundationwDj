import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from animals.models import History
from engagements.models import AnimalEngagement

from .models import CareAction, CareIndicator, VirtualWallet


@login_required
def gamification_dashboard(request, animal_id):
    """
    Vista principal de gamificación para un animal apadrinado.
    Muestra los indicadores y permite realizar acciones de cuidado.
    """
    # Verificar que el usuario tiene un apadrinamiento aprobado para este animal
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",  # Sponsorship
        status="A",  # Approved
    )

    # Obtener o crear el CareIndicator (debería existir por el signal)
    care_indicator, created = CareIndicator.objects.get_or_create(
        engagement=engagement,
        defaults={"food_level": 100, "hygiene_level": 100, "health_level": 100},
    )

    # Obtener o crear la billetera del usuario
    wallet, created = VirtualWallet.objects.get_or_create(
        user=request.user, defaults={"balance": 1000}
    )

    # Obtener el shelter para saber los costos
    shelter = engagement.animal.shelter

    # Calcular costos en monedas virtuales (basado en COP)
    # 1 moneda = 10 COP (según WalletRecharge.calculate_coins)
    food_cost = int(shelter.food_unit_cost / 10)
    hygiene_cost = int(shelter.hygiene_unit_cost / 10)

    # Obtener eventos de salud pendientes o en tratamiento
    health_events = History.objects.filter(
        animal=engagement.animal, status__in=["P", "T"], cost_coins__gt=0
    ).order_by("-is_urgent", "entry_date")

    # Calcular nivel y XP (puedes expandir esto más adelante)
    total_actions = CareAction.objects.filter(care_indicator=care_indicator).count()
    level = min(1 + (total_actions // 10), 20)  # Cada 10 acciones sube un nivel, max 20
    xp_current = (total_actions % 10) * 10  # Progreso hacia el siguiente nivel
    xp_max = 100

    # Historial de acciones recientes
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
        "level": level,
        "xp_current": xp_current,
        "xp_max": xp_max,
        "recent_actions": recent_actions,
    }

    return render(request, "gamifications/dashboard.html", context)


@login_required
@require_POST
def feed_animal(request, animal_id):
    """
    Acción: Dar de comer al animal.
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator = engagement.care_indicator
    wallet = request.user.wallet
    shelter = engagement.animal.shelter

    # Calcular costo
    food_cost = int(shelter.food_unit_cost / 10)

    # Verificar si puede pagar
    if not wallet.can_afford(food_cost):
        return JsonResponse(
            {"success": False, "error": "No tienes suficientes monedas"}, status=400
        )

    # Verificar si el nivel no está al máximo
    if care_indicator.food_level >= 100:
        return JsonResponse(
            {"success": False, "error": "El nivel de alimento ya está al máximo"},
            status=400,
        )

    # Aumentar nivel de comida (configurable, por ahora +10%)
    increase = 10
    old_level = care_indicator.food_level
    care_indicator.food_level = min(100, care_indicator.food_level + increase)
    care_indicator.last_food_update = timezone.now()
    care_indicator.save()

    # Gastar monedas
    wallet.spend_coins(food_cost, f"Alimentar a {engagement.animal.name}")

    # Registrar acción (con XP ganado)
    xp_earned = 10  # Configurable
    CareAction.objects.create(
        care_indicator=care_indicator,
        action_type="F",
        amount_increased=increase,
        coins_spent=food_cost,
        xp_earned=xp_earned,
    )

    return JsonResponse(
        {
            "success": True,
            "new_level": care_indicator.food_level,
            "old_level": old_level,
            "coins_spent": food_cost,
            "new_balance": wallet.balance,
            "xp_earned": xp_earned,
            "message": f"¡{engagement.animal.name} ha comido! +{increase}% alimento",
        }
    )


@login_required
@require_POST
def clean_animal(request, animal_id):
    """
    Acción: Limpiar/higiene del animal.
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator = engagement.care_indicator
    wallet = request.user.wallet
    shelter = engagement.animal.shelter

    # Calcular costo
    hygiene_cost = int(shelter.hygiene_unit_cost / 10)

    # Verificar si puede pagar
    if not wallet.can_afford(hygiene_cost):
        return JsonResponse(
            {"success": False, "error": "No tienes suficientes monedas"}, status=400
        )

    # Verificar si el nivel no está al máximo
    if care_indicator.hygiene_level >= 100:
        return JsonResponse(
            {"success": False, "error": "El nivel de higiene ya está al máximo"},
            status=400,
        )

    # Aumentar nivel de higiene
    increase = 10
    old_level = care_indicator.hygiene_level
    care_indicator.hygiene_level = min(100, care_indicator.hygiene_level + increase)
    care_indicator.last_hygiene_update = timezone.now()
    care_indicator.save()

    # Gastar monedas
    wallet.spend_coins(hygiene_cost, f"Limpiar a {engagement.animal.name}")

    # Registrar acción
    xp_earned = 10
    CareAction.objects.create(
        care_indicator=care_indicator,
        action_type="H",
        amount_increased=increase,
        coins_spent=hygiene_cost,
        xp_earned=xp_earned,
    )

    return JsonResponse(
        {
            "success": True,
            "new_level": care_indicator.hygiene_level,
            "old_level": old_level,
            "coins_spent": hygiene_cost,
            "new_balance": wallet.balance,
            "xp_earned": xp_earned,
            "message": f"¡{engagement.animal.name} está limpio! +{increase}% higiene",
        }
    )


@login_required
@require_POST
def contribute_health(request, animal_id, history_id):
    """
    Acción: Contribuir monedas a un evento de salud.
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator = engagement.care_indicator
    wallet = request.user.wallet

    # Obtener el evento de salud
    health_event = get_object_or_404(
        History, id=history_id, animal=engagement.animal, status__in=["P", "T"]
    )

    # Obtener cantidad a contribuir del request
    try:
        data = json.loads(request.body)
        contribution = int(data.get("amount", 0))
    except:
        contribution = int(request.POST.get("amount", 0))

    if contribution <= 0:
        return JsonResponse(
            {"success": False, "error": "Cantidad inválida"}, status=400
        )

    # Verificar que no contribuya más de lo necesario
    remaining = health_event.remaining_coins
    if contribution > remaining:
        contribution = remaining

    # Verificar si puede pagar
    if not wallet.can_afford(contribution):
        return JsonResponse(
            {"success": False, "error": "No tienes suficientes monedas"}, status=400
        )

    # Gastar monedas
    wallet.spend_coins(
        contribution, f"Tratamiento médico para {engagement.animal.name}"
    )

    # Registrar contribución
    health_event.contribute(contribution)

    # Registrar acción
    xp_earned = contribution // 2  # 0.5 XP por moneda gastada
    CareAction.objects.create(
        care_indicator=care_indicator,
        action_type="M",
        amount_increased=0,  # No aumenta indicador directamente
        coins_spent=contribution,
        xp_earned=xp_earned,
    )

    # Verificar si se completó el financiamiento
    fully_funded = health_event.is_fully_funded

    return JsonResponse(
        {
            "success": True,
            "contribution": contribution,
            "new_balance": wallet.balance,
            "xp_earned": xp_earned,
            "progress": health_event.progress_percentage,
            "remaining": health_event.remaining_coins,
            "fully_funded": fully_funded,
            "message": f"Contribución exitosa: {contribution} monedas",
        }
    )


@login_required
def get_care_status(request, animal_id):
    """
    API para obtener el estado actual de los indicadores (para actualización en tiempo real).
    """
    engagement = get_object_or_404(
        AnimalEngagement,
        animal_id=animal_id,
        user=request.user,
        engagements_type="S",
        status="A",
    )

    care_indicator = engagement.care_indicator
    wallet = request.user.wallet

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

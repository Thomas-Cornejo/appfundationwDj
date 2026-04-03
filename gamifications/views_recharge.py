import hashlib
import json
import time

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from engagements.models import AnimalEngagement
from gamifications.models import PaymentEvent
from gamifications.services.idempotency import generate_idempotency_key
from shelters.models import Shelter

from .models import Wallet, WalletRecharge


@login_required
def recharge_wallet(request, animal_id=None):
    """
    View to display the coin recharge form.
    The user chooses how much they want to recharge.
    If animal_id is provided, pre-select the shelter for that animal.
    """
    packages = [
        {"cop": 10000, "coins": 1000, "bonus": 0, "label": "Básico"},
        {"cop": 20000, "coins": 2000, "bonus": 200, "label": "Popular"},
        {"cop": 50000, "coins": 5000, "bonus": 750, "label": "Avanzado"},
        {"cop": 100000, "coins": 10000, "bonus": 2000, "label": "Premium"},
    ]

    shelters = Shelter.objects.filter(is_active=True)

    selected_shelter_id = None
    from_animal = None
    if animal_id:
        try:
            engagement = AnimalEngagement.objects.get(
                animal_id=animal_id, user=request.user, engagements_type="S", status="A"
            )
            selected_shelter_id = engagement.animal.shelter.id
            from_animal = engagement.animal
        except AnimalEngagement.DoesNotExist:
            messages.warning(request, "No tienes un apadrinamiento activo para este animal.")
    user_wallets = Wallet.objects.filter(user=request.user).select_related("shelter")

    wallet = None
    if selected_shelter_id:
        wallet = user_wallets.filter(shelter_id=selected_shelter_id).first()
        if not wallet:
            wallet = Wallet.objects.create(
                user=request.user, shelter_id=selected_shelter_id, balance=0
            )
    elif user_wallets.exists():
        wallet = user_wallets.first()
    else:
        wallet = type("obj", (object,), {"balance": 0})()

    wompi_key = settings.WOMPI_PUBLIC_KEY.strip()

    context = {
        "user_wallets": user_wallets,
        "wallet": wallet,
        "packages": packages,
        "shelters": shelters,
        "wompi_public_key": wompi_key,
        "selected_shelter_id": selected_shelter_id,
        "from_animal": from_animal,
    }

    return render(request, "gamifications/recharge_wallet.html", context)


@login_required
@require_POST
def create_recharge(request):
    """
    Create a pending recharge and generate the reference for Wompi.
    """
    try:
        amount_cop = int(request.POST.get("amount_cop", "").strip())
    except (ValueError, TypeError):
        return JsonResponse(
            {"success": False, "error": "El monto debe ser un número entero."},
            status=400,
        )

    if amount_cop < 5000:
        return JsonResponse(
            {"success": False, "error": "El monto mínimo de recarga es $5,000 COP"},
            status=400,
        )

    shelter_id = request.POST.get("shelter_id", "").strip()
    if not shelter_id:
        return JsonResponse(
            {"success": False, "error": "Debes seleccionar un albergue."},
            status=400,
        )

    try:
        shelter = get_object_or_404(Shelter, id=shelter_id, is_active=True)

        wallet, _ = Wallet.objects.get_or_create(
            user=request.user,
            shelter=shelter,
            defaults={"balance": 0},
        )

        base_coins = amount_cop // 10
        bonus = 0
        if amount_cop >= 100000:
            bonus = int(base_coins * 0.20)
        elif amount_cop >= 50000:
            bonus = int(base_coins * 0.15)
        elif amount_cop >= 20000:
            bonus = int(base_coins * 0.10)
        total_coins = base_coins + bonus

        idempotency_key = generate_idempotency_key(
            wallet_id=wallet.id,
            shelter_id=shelter.id,
            amount_cop=amount_cop,
            username=request.user.username,
        )

        existing_event = (
            PaymentEvent.objects.filter(idempotency_key=idempotency_key)
            .select_related("recharge")
            .first()
        )
        if existing_event:
            return JsonResponse(
                {
                    "success": False,
                    "idempotent": True,
                    "existing_status": existing_event.status,
                    "existing_recharge_id": existing_event.recharge.id,
                    "error": (
                        "Ya existe un pago con estos datos hoy. "
                        f"Estado actual: {existing_event.get_status_display()}"
                    ),
                },
                status=409,
            )

        payment_method = request.POST.get("payment_method", "WOMPI")
        recharge = WalletRecharge.objects.create(
            wallet=wallet,
            amount_cop=amount_cop,
            coins_received=total_coins,
            payment_method=payment_method,
            status="P",
        )

        timestamp = int(time.time())
        reference = f"RCG{recharge.id}U{request.user.id}T{timestamp}"
        recharge.payment_reference = reference
        recharge.save(update_fields=["payment_reference"])

        PaymentEvent.objects.create(
            recharge=recharge,
            status="PENDING",
            idempotency_key=idempotency_key,
        )

        amount_in_cents = amount_cop * 100
        currency = "COP"
        concatenated_string = (
            f"{reference}{amount_in_cents}{currency}{settings.WOMPI_INTEGRITY_SECRET}"
        )
        integrity_signature = hashlib.sha256(concatenated_string.encode("utf-8")).hexdigest()

        return JsonResponse(
            {
                "success": True,
                "recharge_id": recharge.id,
                "reference": reference,
                "amount_cop": amount_cop,
                "amount_in_cents": amount_in_cents,
                "currency": currency,
                "coins": total_coins,
                "base_coins": base_coins,
                "bonus": bonus,
                "integrity_signature": integrity_signature,
                "shelter_name": shelter.name,
            }
        )

    except Http404:
        return JsonResponse({"success": False, "error": "Albergue no encontrado."}, status=404)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse(
            {"success": False, "error": "Error interno del servidor."},
            status=500,
        )


@csrf_exempt
def wompi_webhook(request):
    """
    Wompi webhook for receiving payment notifications.
    Wompi sends a notification when the payment status changes.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        event = data.get("event")
        signature = data.get("signature", {})

        if not verify_wompi_signature(data, signature):
            return JsonResponse({"error": "Invalid signature"}, status=403)

        if event == "transaction.updated":
            transaction_data = data.get("data", {}).get("transaction", {})
            reference = transaction_data.get("reference")
            status = transaction_data.get("status")
            transaction_id = transaction_data.get("id")

            if reference and reference.startswith("RCG"):
                try:
                    recharge_id = reference.split("U")[0].replace("RCG", "")
                    recharge = WalletRecharge.objects.get(id=recharge_id)

                    if status == "APPROVED":
                        recharge.transaction_id = transaction_id
                        recharge.approve()

                    elif status == "DECLINED" or status == "VOIDED":
                        recharge.status = "R"
                        recharge.transaction_id = transaction_id
                        recharge.save()

                    elif status == "ERROR":
                        recharge.status = "F"
                        recharge.transaction_id = transaction_id
                        recharge.save()

                except WalletRecharge.DoesNotExist:
                    print(f"Recarga no encontrada: {reference}")

        return JsonResponse({"status": "ok"})

    except Exception as e:
        print(f"Error en webhook: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def verify_wompi_signature(data, signature):
    """
    Verify the Wompi webhook signature for security.
    """
    try:
        event = data.get("event")
        timestamp = data.get("timestamp")
        string_to_sign = f"{event}{timestamp}{json.dumps(data.get('data'))}"
        calculated_signature = hashlib.sha256(
            f"{string_to_sign}{settings.WOMPI_EVENT_SECRET}".encode()
        ).hexdigest()

        return calculated_signature == signature.get("checksum")
    except:
        return False


@login_required
def recharge_callback(request):
    """
    Return page after payment.
    Wompi redirects here with the result.
    """
    transaction_id = request.GET.get("id")

    if not transaction_id:
        messages.warning(request, "No se pudo verificar el estado de tu pago.")
        return redirect("gamifications:recharge_wallet")

    try:
        is_sandbox = settings.WOMPI_PUBLIC_KEY.startswith("pub_test")
        api_url = (
            "https://sandbox.wompi.co/v1/transactions"
            if is_sandbox
            else "https://production.wompi.co/v1/transactions"
        )
        response = requests.get(
            f"{api_url}/{transaction_id}",
            headers={"Authorization": f"Bearer {settings.WOMPI_PUBLIC_KEY}"},
            timeout=10,
        )

        if response.status_code == 200:
            transaction_data = response.json()["data"]
            reference = transaction_data.get("reference")
            status = transaction_data.get("status")
            amount_cents = transaction_data.get("amount_in_cents")

            if reference and reference.startswith("RCG"):
                try:
                    recharge_id = reference.split("U")[0].replace("RCG", "")
                    recharge = WalletRecharge.objects.get(id=recharge_id, wallet__user=request.user)

                    context = {
                        "recharge": recharge,
                        "status": status,
                        "transaction_id": transaction_id,
                        "transaction_data": transaction_data,
                    }

                    if status == "APPROVED":
                        if recharge.status != "A":
                            recharge.transaction_id = transaction_id
                            recharge.approve()
                            wallet = recharge.wallet
                            messages.success(
                                request,
                                f"¡Recarga exitosa! Se han agregado {recharge.coins_received} monedas "
                                f"para {wallet.shelter.name}. "
                                f"Tu saldo actual para este albergue es: {wallet.balance} monedas.",
                            )
                        else:
                            messages.info(request, "Esta recarga ya fue procesada anteriormente.")

                    elif status == "DECLINED":
                        recharge.status = "R"
                        recharge.transaction_id = transaction_id
                        recharge.save()
                        messages.error(
                            request,
                            "El pago fue rechazado. Por favor, intenta nuevamente.",
                        )

                    elif status == "PENDING":
                        recharge.transaction_id = transaction_id
                        recharge.save()
                        messages.info(
                            request,
                            "Tu pago está siendo procesado. Te notificaremos cuando esté aprobado.",
                        )

                    elif status == "ERROR":
                        recharge.status = "F"
                        recharge.transaction_id = transaction_id
                        recharge.save()
                        messages.error(request, "Ocurrió un error al procesar tu pago.")

                    return render(request, "gamifications/recharge_callback.html", context)

                except WalletRecharge.DoesNotExist:
                    print(f"Recarga no encontrada para referencia: {reference}")
                    messages.error(
                        request,
                        "No se encontró la recarga asociada a esta transacción.",
                    )
                except Exception as e:
                    print(f"Error procesando recarga: {e}")
                    import traceback

                    traceback.print_exc()
                    messages.error(request, f"Error al procesar la recarga: {str(e)}")
            else:
                messages.warning(request, "Referencia de pago inválida.")

        else:
            messages.error(request, "No se pudo verificar el estado del pago con Wompi.")

    except requests.RequestException as e:
        messages.error(request, "Error de conexión al verificar el pago.")
    except Exception as e:
        import traceback

        traceback.print_exc()
        messages.error(request, f"Error inesperado: {str(e)}")

    return redirect("gamifications:recharge_wallet")


@login_required
def recharge_history(request):
    """
    User recharge history.
    """
    recharges = (
        WalletRecharge.objects.filter(wallet__user=request.user)
        .select_related("wallet__shelter")
        .order_by("-created_at")
    )

    user_wallets = Wallet.objects.filter(user=request.user).select_related("shelter")
    total_coins = user_wallets.aggregate(total=Sum("balance"))["total"] or 0

    total_cop_recharged = (
        recharges.filter(status="A").aggregate(total=Sum("amount_cop"))["total"] or 0
    )

    context = {
        "user_wallets": user_wallets,
        "recharges": recharges,
        "total_coins": total_coins,
        "total_cop_recharged": total_cop_recharged,
    }

    return render(request, "gamifications/recharge_history.html", context)

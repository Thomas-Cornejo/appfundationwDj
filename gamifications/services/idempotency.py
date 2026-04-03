import hashlib
from datetime import date


def generate_idempotency_key(
    wallet_id: int,
    shelter_id: int,
    amount_cop: int,
    username: str,
    day: date = None,
) -> str:
    """
    Generate a deterministic idempotency key for a payment request.

    The key is derived from the payment attributes and a daily time component,
    ensuring that identical requests within the same day produce the same key.

    Args:
    wallet_id: Identifier of the wallet initiating the payment.
    shelter_id: Identifier of the target shelter.
    amount_cop: Payment amount in COP.
    username: Username of the requester.
    day: Optional date used for key generation. Defaults to current date.

    Returns:
    A SHA-256 hash representing the idempotency key.
    """
    if day is None:
        day = date.today()

    payload = f"{wallet_id}:{shelter_id}:{amount_cop}:{username}:{day.isoformat()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

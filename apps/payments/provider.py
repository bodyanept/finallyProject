from __future__ import annotations

from decimal import Decimal
from django.conf import settings


def create_yookassa_payment(order, payment_method: str, return_url: str) -> str:
    shop_id = getattr(settings, 'YOOKASSA_SHOP_ID', '')
    secret_key = getattr(settings, 'YOOKASSA_SECRET_KEY', '')
    if not shop_id or not secret_key:
        raise RuntimeError('YooKassa keys are not configured')

    try:
        from yookassa import Payment, Configuration  # type: ignore
    except Exception as e:
        raise RuntimeError('YooKassa SDK is not installed') from e

    Configuration.account_id = shop_id
    Configuration.secret_key = secret_key

    amount_value = str(Decimal(order.total))

    payment_method_data = None
    if payment_method == 'sbp':
        payment_method_data = {"type": "sbp"}
    elif payment_method == 'card':
        payment_method_data = {"type": "bank_card"}

    create_payload = {
        "amount": {"value": amount_value, "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "metadata": {"order_id": order.id},
        "description": f"Order #{order.id}",
    }
    if payment_method_data:
        create_payload["payment_method_data"] = payment_method_data

    payment = Payment.create(create_payload)
    confirmation = getattr(payment, 'confirmation', None)
    confirmation_url = getattr(confirmation, 'confirmation_url', None)
    if not confirmation_url:
        raise RuntimeError('No confirmation URL from YooKassa')
    return confirmation_url

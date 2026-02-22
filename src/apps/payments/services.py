"""Paystack API client service."""

import hashlib
import hmac
import logging
import uuid

from django.conf import settings

logger = logging.getLogger(__name__)

PAYSTACK_API_URL = "https://api.paystack.co"


def get_paystack_secret_key() -> str:
    """Return the Paystack secret key from settings."""
    return getattr(settings, "PAYSTACK_SECRET_KEY", "")


def get_paystack_public_key() -> str:
    """Return the Paystack public key from settings."""
    return getattr(settings, "PAYSTACK_PUBLIC_KEY", "")


def generate_reference() -> str:
    """Generate a unique payment reference."""
    return f"acoruss-{uuid.uuid4().hex[:12]}"


def _make_paystack_request(
    *,
    endpoint: str,
    method: str = "GET",
    data: bytes | None = None,
) -> dict:
    """Synchronous Paystack API request (for use in executors)."""
    import json
    from urllib.request import Request, urlopen

    secret_key = get_paystack_secret_key()
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }
    url = f"{PAYSTACK_API_URL}{endpoint}"
    req = Request(url, data=data, headers=headers, method=method)  # noqa: S310
    response = urlopen(req, timeout=30)  # noqa: S310
    return json.loads(response.read())


async def initialise_transaction(
    *,
    email: str,
    amount_kobo: int,
    reference: str,
    currency: str = "KES",
    callback_url: str = "",
    metadata: dict | None = None,
) -> dict:
    """
    Initialise a Paystack transaction.

    Args:
        email: Customer email address.
        amount_kobo: Amount in smallest currency unit.
        reference: Unique transaction reference.
        currency: Currency code (KES, USD, NGN).
        callback_url: URL to redirect after payment.
        metadata: Additional metadata for the transaction.

    Returns:
        Paystack API response data dict.

    """
    import asyncio
    import json
    from urllib.request import Request, urlopen

    secret_key = get_paystack_secret_key()
    if not secret_key:
        logger.warning("Paystack secret key not configured")
        return {"status": False, "message": "Payment not configured"}

    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
        "currency": currency,
    }
    if callback_url:
        payload["callback_url"] = callback_url
    if metadata:
        payload["metadata"] = metadata

    data = json.dumps(payload).encode()
    req = Request(  # noqa: S310
        f"{PAYSTACK_API_URL}/transaction/initialize",
        data=data,
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        },
    )

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(
            None,
            lambda: urlopen(req, timeout=30).read(),  # noqa: S310
        )
        return json.loads(response)
    except Exception:
        logger.exception("Failed to initialise Paystack transaction")
        return {"status": False, "message": "Payment initiation failed"}


async def verify_transaction(reference: str) -> dict:
    """
    Verify a Paystack transaction by reference.

    Returns:
        Paystack API response data dict.

    """
    import asyncio
    import json
    from urllib.request import Request, urlopen

    secret_key = get_paystack_secret_key()
    if not secret_key:
        return {"status": False, "message": "Payment not configured"}

    req = Request(  # noqa: S310
        f"{PAYSTACK_API_URL}/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {secret_key}"},
    )

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(
            None,
            lambda: urlopen(req, timeout=30).read(),  # noqa: S310
        )
        return json.loads(response)
    except Exception:
        logger.exception("Failed to verify Paystack transaction: %s", reference)
        return {"status": False, "message": "Verification failed"}


async def create_refund(
    *,
    transaction_reference: str,
    amount_kobo: int | None = None,
    reason: str = "",
    merchant_note: str = "",
) -> dict:
    """
    Create a refund on Paystack.

    Args:
        transaction_reference: The transaction reference to refund.
        amount_kobo: Amount to refund in smallest unit. None = full refund.
        reason: Customer-facing reason for the refund.
        merchant_note: Internal note for the merchant.

    Returns:
        Paystack API response data dict.

    """
    import asyncio
    import json
    from urllib.request import Request, urlopen

    secret_key = get_paystack_secret_key()
    if not secret_key:
        return {"status": False, "message": "Payment not configured"}

    payload: dict = {"transaction": transaction_reference}
    if amount_kobo is not None:
        payload["amount"] = amount_kobo
    if reason:
        payload["customer_note"] = reason
    if merchant_note:
        payload["merchant_note"] = merchant_note

    data = json.dumps(payload).encode()
    req = Request(  # noqa: S310
        f"{PAYSTACK_API_URL}/refund",
        data=data,
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        },
    )

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(
            None,
            lambda: urlopen(req, timeout=30).read(),  # noqa: S310
        )
        return json.loads(response)
    except Exception:
        logger.exception("Failed to create refund for: %s", transaction_reference)
        return {"status": False, "message": "Refund request failed"}


async def fetch_transaction_details(transaction_id: str) -> dict:
    """
    Fetch full transaction details from Paystack by transaction ID.

    Returns:
        Paystack API response data dict including fees, channel, etc.

    """
    import asyncio

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(
            None,
            lambda: _make_paystack_request(endpoint=f"/transaction/{transaction_id}"),
        )
    except Exception:
        logger.exception("Failed to fetch transaction details: %s", transaction_id)
        return {"status": False, "message": "Could not fetch transaction details"}


def validate_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Validate the Paystack webhook signature.

    Args:
        payload: Raw request body bytes.
        signature: x-paystack-signature header value.

    Returns:
        True if signature is valid.

    """
    secret_key = get_paystack_secret_key()
    if not secret_key:
        return False

    expected = hmac.new(
        secret_key.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

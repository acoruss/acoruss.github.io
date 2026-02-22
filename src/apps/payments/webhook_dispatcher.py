"""Outbound webhook dispatcher for notifying external services."""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import ClassVar

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS: ClassVar[list[int]] = [1, 5, 25]


def sign_payload(payload: bytes, secret: str) -> str:
    """Create HMAC SHA256 signature for webhook payload."""
    return hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


async def dispatch_webhook(
    *,
    service,
    payment,
    event: str = "payment.success",
) -> bool:
    """
    Send webhook notification to an external service.

    Retries up to MAX_RETRIES times with exponential backoff.
    Returns True if delivery was successful.
    """
    from .models import WebhookDeliveryLog

    if not service.webhook_url:
        logger.info("No webhook URL for service %s, skipping", service.name)
        return False

    payload_data = {
        "event": event,
        "data": {
            "reference": payment.reference,
            "service_reference": payment.service_reference,
            "email": payment.email,
            "name": payment.name,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "status": payment.status,
            "channel": payment.channel,
            "fees": str(payment.fees),
            "description": payment.description,
            "refund_status": payment.refund_status,
            "refunded_amount": str(payment.refunded_amount),
            "metadata": payment.metadata,
            "created_at": payment.created_at.isoformat(),
        },
    }

    payload_bytes = json.dumps(payload_data).encode()
    signature = sign_payload(payload_bytes, service.api_secret)

    headers = {
        "Content-Type": "application/json",
        "X-Acoruss-Signature": signature,
        "X-Acoruss-Event": event,
        "User-Agent": "Acoruss-Payments/1.0",
    }

    loop = asyncio.get_event_loop()

    for attempt in range(1, MAX_RETRIES + 1):
        start_time = time.monotonic()
        log_entry = await WebhookDeliveryLog.objects.acreate(
            service=service,
            payment=payment,
            url=service.webhook_url,
            event=event,
            request_headers=dict(headers),
            request_body=payload_data,
            attempt=attempt,
        )

        try:
            from urllib.request import Request, urlopen

            req = Request(  # noqa: S310
                service.webhook_url,
                data=payload_bytes,
                headers=headers,
                method="POST",
            )

            _req = req  # Bind loop variable for closure
            response = await loop.run_in_executor(
                None,
                lambda _r=_req: urlopen(_r, timeout=15),  # noqa: S310
            )

            duration_ms = int((time.monotonic() - start_time) * 1000)
            response_body = response.read().decode(errors="replace")[:2000]

            log_entry.response_status = response.status
            log_entry.response_body = response_body
            log_entry.duration_ms = duration_ms
            log_entry.success = 200 <= response.status < 300
            await log_entry.asave(
                update_fields=[
                    "response_status",
                    "response_body",
                    "duration_ms",
                    "success",
                ]
            )

            if log_entry.success:
                from django.utils import timezone

                payment.webhook_delivered = True
                payment.webhook_delivered_at = timezone.now()
                await payment.asave(update_fields=["webhook_delivered", "webhook_delivered_at", "updated_at"])
                logger.info(
                    "Webhook delivered for %s to %s (attempt %d)",
                    payment.reference,
                    service.name,
                    attempt,
                )
                return True

            logger.warning(
                "Webhook delivery failed for %s (attempt %d, status %d)",
                payment.reference,
                attempt,
                response.status,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            log_entry.duration_ms = duration_ms
            log_entry.error_message = str(exc)[:500]
            await log_entry.asave(update_fields=["duration_ms", "error_message"])

            logger.warning(
                "Webhook delivery error for %s (attempt %d): %s",
                payment.reference,
                attempt,
                exc,
            )

        # Wait before retry (skip wait on last attempt)
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAYS[attempt - 1])

    logger.error(
        "Webhook delivery failed after %d attempts for %s to %s",
        MAX_RETRIES,
        payment.reference,
        service.name,
    )
    return False

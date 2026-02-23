"""API views for service-to-service payment integration."""

import json
import logging

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from . import services
from .api_auth import ServiceAuthMixin, get_client_ip
from .models import Payment

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class APIInitiatePaymentView(ServiceAuthMixin, View):
    """API: Initiate a payment from an external service."""

    async def post(self, request: HttpRequest) -> JsonResponse:
        """Create a payment and return a Paystack authorization URL."""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        email = str(data.get("email", "")).strip()
        name = str(data.get("name", "")).strip()
        amount_raw = data.get("amount")
        currency = str(data.get("currency", "KES")).upper()
        description = str(data.get("description", "")).strip()
        service_reference = str(data.get("service_reference", "")).strip()
        callback_url = str(data.get("callback_url", "")).strip() or request.service.default_callback_url
        metadata = data.get("metadata") or {}
        idempotency_key = str(data.get("idempotency_key", "")).strip()

        # --- validation ---
        errors: dict[str, str] = {}
        if not email:
            errors["email"] = "Required"
        try:
            amount = round(float(amount_raw), 2)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            errors["amount"] = "Must be a positive number"
            amount = 0.0
        if currency not in dict(Payment.Currency.choices):
            errors["currency"] = f"Must be one of: {', '.join(dict(Payment.Currency.choices).keys())}"
        if request.service.allowed_currencies and currency not in request.service.allowed_currencies:
            errors["currency"] = (
                f"Not allowed for this service. Allowed: {', '.join(request.service.allowed_currencies)}"
            )
        if errors:
            return JsonResponse({"error": "Validation failed", "details": errors}, status=400)

        # --- idempotency ---
        if idempotency_key:
            existing = await Payment.objects.filter(
                idempotency_key=idempotency_key,
                service=request.service,
            ).afirst()
            if existing:
                return JsonResponse(
                    {
                        "status": True,
                        "message": "Payment already exists (idempotent)",
                        "data": {
                            "reference": existing.reference,
                            "authorization_url": existing.authorization_url,
                            "status": existing.status,
                        },
                    }
                )

        reference = services.generate_reference()

        payment = await Payment.objects.acreate(
            service=request.service,
            service_reference=service_reference,
            email=email,
            name=name,
            amount=amount,
            currency=currency,
            description=description,
            reference=reference,
            callback_url=callback_url,
            idempotency_key=idempotency_key,
            ip_address=get_client_ip(request),
            metadata={
                "service": request.service.slug,
                "service_reference": service_reference,
                **(metadata if isinstance(metadata, dict) else {}),
            },
        )

        # Tell Paystack to redirect back to Acoruss (not the external service)
        paystack_callback = f"{settings.SITE_URL}/payments/verify/"

        result = await services.initialise_transaction(
            email=email,
            amount_kobo=payment.amount_in_kobo,
            reference=reference,
            currency=currency,
            callback_url=paystack_callback,
            metadata={
                "payment_id": payment.pk,
                "service": request.service.slug,
                "service_reference": service_reference,
                "description": description,
            },
        )

        if result.get("status") and result.get("data", {}).get("authorization_url"):
            auth_url = result["data"]["authorization_url"]
            payment.authorization_url = auth_url
            await payment.asave(update_fields=["authorization_url", "updated_at"])
            return JsonResponse(
                {
                    "status": True,
                    "message": "Payment initiated",
                    "data": {
                        "reference": reference,
                        "authorization_url": auth_url,
                        "callback_url": callback_url,
                    },
                }
            )

        paystack_message = result.get("message", "Could not initiate payment with Paystack")
        logger.error("Paystack initiation failed: %s | full response: %s", paystack_message, result)
        return JsonResponse(
            {"status": False, "message": paystack_message},
            status=502,
        )


@method_decorator(csrf_exempt, name="dispatch")
class APIPaymentStatusView(ServiceAuthMixin, View):
    """API: Check payment status by reference."""

    async def get(self, request: HttpRequest, reference: str) -> JsonResponse:
        """Return current payment status."""
        try:
            payment = await Payment.objects.select_related("service").aget(
                reference=reference,
                service=request.service,
            )
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment not found"}, status=404)

        return JsonResponse(
            {
                "status": True,
                "data": {
                    "reference": payment.reference,
                    "service_reference": payment.service_reference,
                    "email": payment.email,
                    "name": payment.name,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "description": payment.description,
                    "status": payment.status,
                    "channel": payment.channel,
                    "fees": str(payment.fees),
                    "net_amount": str(payment.net_amount),
                    "refund_status": payment.refund_status,
                    "refunded_amount": str(payment.refunded_amount),
                    "created_at": payment.created_at.isoformat(),
                    "updated_at": payment.updated_at.isoformat(),
                },
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class APIPaymentListView(ServiceAuthMixin, View):
    """API: List payments belonging to the authenticated service."""

    async def get(self, request: HttpRequest) -> JsonResponse:
        """Return paginated list of payments."""
        qs = Payment.objects.filter(service=request.service)

        status = request.GET.get("status")
        if status and status in dict(Payment.Status.choices):
            qs = qs.filter(status=status)

        email = request.GET.get("email")
        if email:
            qs = qs.filter(email=email)

        page = max(int(request.GET.get("page", 1)), 1)
        per_page = min(max(int(request.GET.get("per_page", 20)), 1), 100)
        offset = (page - 1) * per_page

        total = await qs.acount()
        payments = []
        async for payment in qs[offset : offset + per_page]:
            payments.append(
                {
                    "reference": payment.reference,
                    "service_reference": payment.service_reference,
                    "email": payment.email,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "status": payment.status,
                    "refund_status": payment.refund_status,
                    "created_at": payment.created_at.isoformat(),
                }
            )

        return JsonResponse(
            {
                "status": True,
                "data": payments,
                "meta": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": max((total + per_page - 1) // per_page, 1),
                },
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class APIRefundView(ServiceAuthMixin, View):
    """API: Request a refund for a payment."""

    async def post(self, request: HttpRequest, reference: str) -> JsonResponse:
        """Initiate a full or partial refund."""
        try:
            payment = await Payment.objects.select_related("service").aget(
                reference=reference,
                service=request.service,
            )
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment not found"}, status=404)

        if not payment.is_refundable:
            return JsonResponse({"error": "Payment is not refundable"}, status=400)

        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = {}

        amount_raw = data.get("amount")
        reason = str(data.get("reason", "")).strip()

        amount_kobo: int | None = None
        if amount_raw is not None:
            try:
                refund_amount = round(float(amount_raw), 2)
                if refund_amount <= 0 or refund_amount > float(payment.refundable_amount):
                    return JsonResponse(
                        {"error": f"Refund amount must be between 0.01 and {payment.refundable_amount}"},
                        status=400,
                    )
                amount_kobo = int(refund_amount * 100)
            except (ValueError, TypeError):
                return JsonResponse({"error": "Invalid refund amount"}, status=400)

        result = await services.create_refund(
            transaction_reference=payment.reference,
            amount_kobo=amount_kobo,
            reason=reason,
        )

        if result.get("status"):
            from decimal import Decimal

            refund_data = result.get("data", {})
            refunded = Decimal(str(refund_data.get("amount", 0))) / 100
            payment.refunded_amount += refunded
            payment.paystack_refund_id = str(refund_data.get("id", ""))
            if payment.refunded_amount >= payment.amount:
                payment.refund_status = Payment.RefundStatus.FULL
            else:
                payment.refund_status = Payment.RefundStatus.PARTIAL
            await payment.asave(
                update_fields=[
                    "refunded_amount",
                    "refund_status",
                    "paystack_refund_id",
                    "updated_at",
                ]
            )

            # Notify service via webhook
            if payment.service:
                from .webhook_dispatcher import dispatch_webhook

                await dispatch_webhook(
                    service=payment.service,
                    payment=payment,
                    event="payment.refunded",
                )

            return JsonResponse(
                {
                    "status": True,
                    "message": "Refund initiated",
                    "data": {
                        "reference": payment.reference,
                        "refund_status": payment.refund_status,
                        "refunded_amount": str(payment.refunded_amount),
                        "refundable_amount": str(payment.refundable_amount),
                    },
                }
            )

        return JsonResponse(
            {"status": False, "message": result.get("message", "Refund failed")},
            status=502,
        )

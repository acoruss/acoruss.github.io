"""Payment views for Paystack integration."""

import json
import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from . import services
from .models import Payment

logger = logging.getLogger(__name__)


class PaymentPageView(TemplateView):
    """Public payment page for discovery call / service payments."""

    template_name = "payments/pay.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["paystack_public_key"] = services.get_paystack_public_key()
        return context


class InitiatePaymentView(View):
    """Initiate a Paystack payment transaction."""

    async def post(self, request: HttpRequest) -> HttpResponse:
        email = request.POST.get("email", "").strip()
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "Discovery Call")
        amount_str = request.POST.get("amount", "0")
        currency = request.POST.get("currency", "KES")

        try:
            amount = round(float(amount_str), 2)
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount.")
            return redirect("payments:pay")

        if not email or amount <= 0:
            messages.error(request, "Please provide a valid email and amount.")
            return redirect("payments:pay")

        reference = services.generate_reference()
        callback_url = f"{settings.SITE_URL}/payments/verify/"

        # Create payment record
        payment = await Payment.objects.acreate(
            email=email,
            name=name,
            amount=amount,
            currency=currency,
            description=description,
            reference=reference,
            metadata={"source": "payment_page"},
        )

        # Initialise Paystack transaction
        result = await services.initialise_transaction(
            email=email,
            amount_kobo=payment.amount_in_kobo,
            reference=reference,
            currency=currency,
            callback_url=callback_url,
            metadata={"payment_id": payment.pk, "description": description},
        )

        if result.get("status") and result.get("data", {}).get("authorization_url"):
            authorization_url = result["data"]["authorization_url"]
            payment.authorization_url = authorization_url
            await payment.asave(update_fields=["authorization_url", "updated_at"])
            return redirect(authorization_url)

        messages.error(request, "Could not initiate payment. Please try again.")
        return redirect("payments:pay")


class VerifyPaymentView(View):
    """Handle Paystack callback after payment."""

    async def get(self, request: HttpRequest) -> HttpResponse:
        reference = request.GET.get("reference", "")
        if not reference:
            messages.error(request, "No payment reference provided.")
            return redirect("payments:pay")

        try:
            payment = await Payment.objects.aget(reference=reference)
        except Payment.DoesNotExist:
            messages.error(request, "Payment not found.")
            return redirect("payments:pay")

        # Verify with Paystack
        result = await services.verify_transaction(reference)

        if result.get("status") and result.get("data", {}).get("status") == "success":
            payment.status = Payment.Status.SUCCESS
            payment.paystack_id = str(result["data"].get("id", ""))
            await payment.asave(update_fields=["status", "paystack_id", "updated_at"])
            messages.success(request, "Payment successful! Thank you.")
        else:
            paystack_status = result.get("data", {}).get("status", "failed")
            payment.status = Payment.Status.ABANDONED if paystack_status == "abandoned" else Payment.Status.FAILED
            await payment.asave(update_fields=["status", "updated_at"])
            messages.error(request, "Payment was not successful. Please try again.")

        return redirect("payments:pay")


@method_decorator(csrf_exempt, name="dispatch")
class PaystackWebhookView(View):
    """Handle Paystack webhook events."""

    async def post(self, request: HttpRequest) -> JsonResponse:
        signature = request.headers.get("x-paystack-signature", "")
        if not services.validate_webhook_signature(request.body, signature):
            logger.warning("Invalid Paystack webhook signature")
            return JsonResponse({"error": "Invalid signature"}, status=400)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        event = payload.get("event", "")
        data = payload.get("data", {})

        if event == "charge.success":
            await self._handle_charge_success(data)

        return JsonResponse({"status": "ok"})

    async def _handle_charge_success(self, data: dict) -> None:
        """Handle a successful charge event."""
        reference = data.get("reference", "")
        if not reference:
            return

        try:
            payment = await Payment.objects.aget(reference=reference)
        except Payment.DoesNotExist:
            logger.warning("Webhook received for unknown reference: %s", reference)
            return

        payment.status = Payment.Status.SUCCESS
        payment.paystack_id = str(data.get("id", ""))
        await payment.asave(update_fields=["status", "paystack_id", "updated_at"])
        logger.info("Payment %s marked as successful via webhook", reference)

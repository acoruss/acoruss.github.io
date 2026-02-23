"""Payment views — public payment pages, Paystack webhooks, and dashboard management."""

import csv
import json
import logging
from decimal import Decimal
from typing import ClassVar

from django.conf import settings
from django.contrib import messages
from django.db import models
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from apps.core.views import AdminRequiredMixin

from . import services
from .models import Payment, ServiceProduct, WebhookDeliveryLog

logger = logging.getLogger(__name__)


# ───────────────────────────── Public Payment Pages ──────────────────────────


class PaymentPageView(TemplateView):
    """Public payment page for discovery call / service payments."""

    template_name = "payments/pay.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["paystack_public_key"] = services.get_paystack_public_key()
        return context


class InitiatePaymentView(View):
    """Initiate a Paystack payment transaction (public form)."""

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

        payment = await Payment.objects.acreate(
            email=email,
            name=name,
            amount=amount,
            currency=currency,
            description=description,
            reference=reference,
            metadata={"source": "payment_page"},
        )

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
            payment = await Payment.objects.select_related("service").aget(reference=reference)
        except Payment.DoesNotExist:
            messages.error(request, "Payment not found.")
            return redirect("payments:pay")

        result = await services.verify_transaction(reference)

        if result.get("status") and result.get("data", {}).get("status") == "success":
            payment.status = Payment.Status.SUCCESS
            payment.paystack_id = str(result["data"].get("id", ""))
            # Capture channel and fees from Paystack response
            payment.channel = result["data"].get("channel", "")
            fees_kobo = result["data"].get("fees", 0)
            payment.fees = Decimal(str(fees_kobo)) / 100
            await payment.asave(update_fields=["status", "paystack_id", "channel", "fees", "updated_at"])

            # Dispatch webhook to external service if applicable
            if payment.service_id:
                service = payment.service or await ServiceProduct.objects.aget(pk=payment.service_id)
                from .webhook_dispatcher import dispatch_webhook

                await dispatch_webhook(service=service, payment=payment, event="payment.success")
        else:
            paystack_status = result.get("data", {}).get("status", "failed")
            payment.status = Payment.Status.ABANDONED if paystack_status == "abandoned" else Payment.Status.FAILED
            await payment.asave(update_fields=["status", "updated_at"])

        # Redirect to the service's callback URL if set, otherwise payment page
        if payment.callback_url:
            separator = "&" if "?" in payment.callback_url else "?"
            redirect_url = f"{payment.callback_url}{separator}reference={payment.reference}&status={payment.status}"
            return redirect(redirect_url)

        # Only show flash messages for direct payments (no external redirect)
        if payment.is_successful:
            messages.success(request, "Payment successful! Thank you.")
        else:
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
        elif event == "refund.processed":
            await self._handle_refund(data)

        return JsonResponse({"status": "ok"})

    async def _handle_charge_success(self, data: dict) -> None:
        """Handle a successful charge event."""
        reference = data.get("reference", "")
        if not reference:
            return

        try:
            payment = await Payment.objects.select_related("service").aget(reference=reference)
        except Payment.DoesNotExist:
            logger.warning("Webhook received for unknown reference: %s", reference)
            return

        payment.status = Payment.Status.SUCCESS
        payment.paystack_id = str(data.get("id", ""))
        payment.channel = data.get("channel", "")
        fees_kobo = data.get("fees", 0)
        payment.fees = Decimal(str(fees_kobo)) / 100
        await payment.asave(update_fields=["status", "paystack_id", "channel", "fees", "updated_at"])
        logger.info("Payment %s marked as successful via webhook", reference)

        # Dispatch to external service
        if payment.service:
            from .webhook_dispatcher import dispatch_webhook

            await dispatch_webhook(service=payment.service, payment=payment, event="payment.success")

    async def _handle_refund(self, data: dict) -> None:
        """Handle a refund.processed event."""
        transaction = data.get("transaction", {})
        reference = transaction.get("reference", "") if isinstance(transaction, dict) else ""
        if not reference:
            return

        try:
            payment = await Payment.objects.select_related("service").aget(reference=reference)
        except Payment.DoesNotExist:
            return

        refunded_kobo = data.get("amount", 0)
        payment.refunded_amount = Decimal(str(refunded_kobo)) / 100
        payment.paystack_refund_id = str(data.get("id", ""))
        if payment.refunded_amount >= payment.amount:
            payment.refund_status = Payment.RefundStatus.FULL
        else:
            payment.refund_status = Payment.RefundStatus.PARTIAL
        await payment.asave(update_fields=["refunded_amount", "refund_status", "paystack_refund_id", "updated_at"])
        logger.info("Refund processed for %s", reference)

        if payment.service:
            from .webhook_dispatcher import dispatch_webhook

            await dispatch_webhook(service=payment.service, payment=payment, event="payment.refunded")


# ───────────────── Dashboard: Service / Product Management ───────────────────


class ServiceListView(AdminRequiredMixin, ListView):
    """Dashboard view listing all registered service products."""

    model = ServiceProduct
    template_name = "dashboard/services/list.html"
    context_object_name = "services"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(models.Q(name__icontains=search) | models.Q(slug__icontains=search))
        status = self.request.GET.get("status")
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)
        return qs.annotate(
            payment_count=models.Count("payments"),
            successful_payments=models.Count("payments", filter=models.Q(payments__status=Payment.Status.SUCCESS)),
            total_revenue=models.Sum(
                "payments__amount",
                filter=models.Q(payments__status=Payment.Status.SUCCESS),
                default=Decimal("0.00"),
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_services"] = ServiceProduct.objects.count()
        context["active_services"] = ServiceProduct.objects.filter(is_active=True).count()
        context["search_query"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "all")
        return context


class ServiceCreateView(AdminRequiredMixin, CreateView):
    """Dashboard view to onboard a new service product."""

    model = ServiceProduct
    template_name = "dashboard/services/create.html"
    fields: ClassVar[list[str]] = [
        "name",
        "slug",
        "description",
        "webhook_url",
        "default_callback_url",
        "contact_email",
        "logo_url",
        "allowed_currencies",
        "allowed_ips",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["currency_choices"] = Payment.Currency.choices
        return context

    def form_valid(self, form):
        """Save the service and show the generated credentials."""
        self.object = form.save()
        messages.success(
            self.request,
            f"Service '{self.object.name}' created! API credentials generated.",
        )
        return redirect("core:dashboard_service_detail", slug=self.object.slug)


class ServiceDetailView(AdminRequiredMixin, DetailView):
    """Dashboard detail view for a service product."""

    model = ServiceProduct
    template_name = "dashboard/services/detail.html"
    context_object_name = "service"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object
        payments_qs = Payment.objects.filter(service=service)

        # Stats
        context["total_payments"] = payments_qs.count()
        context["successful_payments"] = payments_qs.filter(status=Payment.Status.SUCCESS).count()
        context["pending_payments"] = payments_qs.filter(status=Payment.Status.PENDING).count()
        context["failed_payments"] = payments_qs.filter(
            status__in=[Payment.Status.FAILED, Payment.Status.ABANDONED]
        ).count()

        # Revenue
        revenue_agg = payments_qs.filter(status=Payment.Status.SUCCESS).aggregate(
            total_revenue=Sum("amount", default=Decimal("0.00")),
            total_fees=Sum("fees", default=Decimal("0.00")),
            total_refunded=Sum("refunded_amount", default=Decimal("0.00")),
        )
        context["total_revenue"] = revenue_agg["total_revenue"]
        context["total_fees"] = revenue_agg["total_fees"]
        context["total_refunded"] = revenue_agg["total_refunded"]
        context["net_revenue"] = (
            revenue_agg["total_revenue"] - revenue_agg["total_fees"] - revenue_agg["total_refunded"]
        )

        # Revenue by currency
        context["revenue_by_currency"] = (
            payments_qs.filter(status=Payment.Status.SUCCESS)
            .values("currency")
            .annotate(
                revenue=Sum("amount", default=Decimal("0.00")),
                fees=Sum("fees", default=Decimal("0.00")),
                count=models.Count("id"),
            )
            .order_by("-revenue")
        )

        # Recent transactions
        context["recent_payments"] = payments_qs[:10]

        # Recent webhook logs
        context["recent_webhooks"] = WebhookDeliveryLog.objects.filter(service=service)[:10]

        return context


class ServiceToggleActiveView(AdminRequiredMixin, View):
    """Toggle a service product's active status."""

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        service = get_object_or_404(ServiceProduct, slug=slug)
        service.is_active = not service.is_active
        service.save(update_fields=["is_active", "updated_at"])
        status = "enabled" if service.is_active else "disabled"
        messages.success(request, f"Service '{service.name}' {status}.")
        return redirect("core:dashboard_service_detail", slug=slug)


class ServiceRegenerateKeysView(AdminRequiredMixin, View):
    """Regenerate API credentials for a service product."""

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        service = get_object_or_404(ServiceProduct, slug=slug)
        service.regenerate_credentials()
        messages.success(request, f"API credentials regenerated for '{service.name}'.")
        return redirect("core:dashboard_service_detail", slug=slug)


class ServiceUpdateView(AdminRequiredMixin, View):
    """Update service settings (webhook URL, callback URL, etc.)."""

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        service = get_object_or_404(ServiceProduct, slug=slug)

        webhook_url = request.POST.get("webhook_url", "").strip()
        default_callback_url = request.POST.get("default_callback_url", "").strip()
        contact_email = request.POST.get("contact_email", "").strip()
        allowed_currencies_raw = request.POST.get("allowed_currencies", "").strip()
        allowed_ips_raw = request.POST.get("allowed_ips", "").strip()

        service.webhook_url = webhook_url
        service.default_callback_url = default_callback_url
        service.contact_email = contact_email

        if allowed_currencies_raw:
            service.allowed_currencies = [c.strip().upper() for c in allowed_currencies_raw.split(",") if c.strip()]
        else:
            service.allowed_currencies = []

        if allowed_ips_raw:
            service.allowed_ips = [ip.strip() for ip in allowed_ips_raw.split(",") if ip.strip()]
        else:
            service.allowed_ips = []

        service.save(
            update_fields=[
                "webhook_url",
                "default_callback_url",
                "contact_email",
                "allowed_currencies",
                "allowed_ips",
                "updated_at",
            ]
        )
        messages.success(request, "Service settings updated.")
        return redirect("core:dashboard_service_detail", slug=slug)


# ──────────────────── Dashboard: Payment Detail & Refund ─────────────────────


class PaymentDetailView(AdminRequiredMixin, DetailView):
    """Dashboard detail view for a single payment transaction."""

    model = Payment
    template_name = "dashboard/payments/detail.html"
    context_object_name = "payment"

    def get_queryset(self):
        return Payment.objects.select_related("service")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["webhook_logs"] = WebhookDeliveryLog.objects.filter(payment=self.object).order_by("-created_at")[:20]
        return context


class PaymentRefundView(AdminRequiredMixin, View):
    """Dashboard action to initiate a refund for a payment."""

    async def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        try:
            payment = await Payment.objects.select_related("service").aget(pk=pk)
        except Payment.DoesNotExist:
            messages.error(request, "Payment not found.")
            return redirect("core:dashboard_payments")

        if not payment.is_refundable:
            messages.error(request, "This payment cannot be refunded.")
            return redirect("core:dashboard_payment_detail", pk=pk)

        amount_str = request.POST.get("refund_amount", "").strip()
        reason = request.POST.get("refund_reason", "").strip()

        amount_kobo: int | None = None
        if amount_str:
            try:
                refund_amount = round(float(amount_str), 2)
                if refund_amount <= 0 or refund_amount > float(payment.refundable_amount):
                    messages.error(
                        request,
                        f"Refund amount must be between 0.01 and {payment.refundable_amount}.",
                    )
                    return redirect("core:dashboard_payment_detail", pk=pk)
                amount_kobo = int(refund_amount * 100)
            except (ValueError, TypeError):
                messages.error(request, "Invalid refund amount.")
                return redirect("core:dashboard_payment_detail", pk=pk)

        result = await services.create_refund(
            transaction_reference=payment.reference,
            amount_kobo=amount_kobo,
            reason=reason,
            merchant_note=f"Initiated by {request.user} from dashboard",
        )

        if result.get("status"):
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

            if payment.service:
                from .webhook_dispatcher import dispatch_webhook

                await dispatch_webhook(
                    service=payment.service,
                    payment=payment,
                    event="payment.refunded",
                )

            messages.success(request, f"Refund of {refunded} initiated successfully.")
        else:
            messages.error(request, f"Refund failed: {result.get('message', 'Unknown error')}")

        return redirect("core:dashboard_payment_detail", pk=pk)


class PaymentExportView(AdminRequiredMixin, View):
    """Export payments as CSV, optionally filtered by service."""

    def get(self, request: HttpRequest) -> HttpResponse:
        qs = Payment.objects.select_related("service").all()

        service_slug = request.GET.get("service")
        if service_slug:
            qs = qs.filter(service__slug=service_slug)

        status = request.GET.get("status")
        if status and status in dict(Payment.Status.choices):
            qs = qs.filter(status=status)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="payments_export.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Reference",
                "Service",
                "Service Ref",
                "Email",
                "Name",
                "Amount",
                "Currency",
                "Fees",
                "Net",
                "Status",
                "Channel",
                "Refund Status",
                "Refunded Amount",
                "Description",
                "Date",
            ]
        )

        for payment in qs.iterator():
            writer.writerow(
                [
                    payment.reference,
                    payment.service.name if payment.service else "Direct",
                    payment.service_reference,
                    payment.email,
                    payment.name,
                    payment.amount,
                    payment.currency,
                    payment.fees,
                    payment.net_amount,
                    payment.status,
                    payment.channel,
                    payment.refund_status,
                    payment.refunded_amount,
                    payment.description,
                    payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        return response

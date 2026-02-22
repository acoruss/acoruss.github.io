"""Payment models for Paystack integration."""

import secrets
from decimal import Decimal
from typing import ClassVar

from django.conf import settings
from django.db import models
from django.utils.text import slugify


def generate_api_key() -> str:
    """Generate a secure API key prefixed with ak_."""
    return f"ak_{secrets.token_hex(24)}"


def generate_api_secret() -> str:
    """Generate a secure API secret prefixed with sk_."""
    return f"sk_{secrets.token_hex(32)}"


class ServiceProduct(models.Model):
    """A product/service registered to use Acoruss payments."""

    name = models.CharField("service name", max_length=255)
    slug = models.SlugField("slug", unique=True, max_length=100)
    description = models.TextField("description", blank=True)

    # Auth credentials (auto-generated)
    api_key = models.CharField(
        "API key",
        max_length=64,
        unique=True,
        db_index=True,
        default=generate_api_key,
    )
    api_secret = models.CharField(
        "API secret",
        max_length=80,
        default=generate_api_secret,
    )

    # Callback config
    webhook_url = models.URLField(
        "webhook callback URL",
        blank=True,
        help_text="URL to receive payment event notifications.",
    )
    default_callback_url = models.URLField(
        "default redirect URL",
        blank=True,
        help_text="Default URL to redirect users after payment.",
    )

    # Settings
    is_active = models.BooleanField("active", default=True)
    allowed_currencies = models.JSONField(
        "allowed currencies",
        default=list,
        blank=True,
        help_text='List of currency codes, e.g. ["KES","USD"]. Empty = all.',
    )

    # Contact
    contact_email = models.EmailField("contact email", blank=True)
    logo_url = models.URLField("logo URL", blank=True)

    # Security
    allowed_ips = models.JSONField(
        "allowed IP addresses",
        default=list,
        blank=True,
        help_text="List of IPs allowed to call the API. Empty = all.",
    )

    # Metadata
    metadata = models.JSONField("metadata", default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField("created", auto_now_add=True)
    updated_at = models.DateTimeField("updated", auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]
        verbose_name = "service product"
        verbose_name_plural = "service products"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not set."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def regenerate_credentials(self) -> tuple[str, str]:
        """Regenerate API key and secret. Returns (new_key, new_secret)."""
        self.api_key = generate_api_key()
        self.api_secret = generate_api_secret()
        self.save(update_fields=["api_key", "api_secret", "updated_at"])
        return self.api_key, self.api_secret


class Payment(models.Model):
    """Records a Paystack payment transaction."""

    class Status(models.TextChoices):
        """Payment status choices."""

        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        ABANDONED = "abandoned", "Abandoned"

    class Currency(models.TextChoices):
        """Supported currency codes."""

        KES = "KES", "Kenyan Shilling"
        USD = "USD", "US Dollar"
        NGN = "NGN", "Nigerian Naira"

    class RefundStatus(models.TextChoices):
        """Refund status choices."""

        NONE = "none", "No Refund"
        PENDING = "pending", "Refund Pending"
        PARTIAL = "partial", "Partially Refunded"
        FULL = "full", "Fully Refunded"
        FAILED = "failed", "Refund Failed"

    # Service link
    service = models.ForeignKey(
        ServiceProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        help_text="The service/product that initiated this payment.",
    )
    service_reference = models.CharField(
        "service reference",
        max_length=255,
        blank=True,
        help_text="External service's order/transaction ID.",
    )

    # Customer info
    email = models.EmailField("customer email")
    name = models.CharField("customer name", max_length=255, blank=True)

    # Payment details
    amount = models.DecimalField(
        "amount",
        max_digits=12,
        decimal_places=2,
        help_text="Amount in the currency's major unit (e.g., KES, USD).",
    )
    currency = models.CharField(
        "currency",
        max_length=3,
        choices=Currency.choices,
        default=Currency.KES,
    )
    description = models.CharField("description", max_length=500, blank=True)

    # Paystack fields
    reference = models.CharField(
        "payment reference",
        max_length=100,
        unique=True,
        db_index=True,
    )
    paystack_id = models.CharField(
        "Paystack transaction ID",
        max_length=100,
        blank=True,
    )
    authorization_url = models.URLField(
        "Paystack authorization URL",
        blank=True,
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    channel = models.CharField(
        "payment channel",
        max_length=50,
        blank=True,
        help_text="Payment channel (card, bank, ussd, etc.)",
    )
    fees = models.DecimalField(
        "Paystack fees",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Fees charged by Paystack.",
    )

    # Callback
    callback_url = models.URLField(
        "payment callback URL",
        blank=True,
        help_text="URL to redirect user after payment.",
    )

    # Refund
    refund_status = models.CharField(
        "refund status",
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.NONE,
    )
    refunded_amount = models.DecimalField(
        "refunded amount",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    paystack_refund_id = models.CharField(
        "Paystack refund ID",
        max_length=100,
        blank=True,
    )

    # Webhook delivery
    webhook_delivered = models.BooleanField("webhook delivered", default=False)
    webhook_delivered_at = models.DateTimeField(
        "webhook delivered at",
        null=True,
        blank=True,
    )

    # Security
    ip_address = models.GenericIPAddressField("client IP", null=True, blank=True)
    idempotency_key = models.CharField(
        "idempotency key",
        max_length=100,
        blank=True,
        db_index=True,
    )

    # Metadata
    metadata = models.JSONField("metadata", default=dict, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )

    # Timestamps
    created_at = models.DateTimeField("created", auto_now_add=True)
    updated_at = models.DateTimeField("updated", auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]
        verbose_name = "payment"
        verbose_name_plural = "payments"

    def __str__(self) -> str:
        service_name = self.service.name if self.service_id else "Direct"
        return f"[{service_name}] {self.reference} - {self.currency} {self.amount} ({self.status})"

    @property
    def amount_in_kobo(self) -> int:
        """Return amount in the smallest currency unit (kobo/cents) for Paystack API."""
        return int(self.amount * 100)

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == self.Status.SUCCESS

    @property
    def net_amount(self) -> Decimal:
        """Amount after Paystack fees."""
        return self.amount - self.fees

    @property
    def refundable_amount(self) -> Decimal:
        """Maximum amount that can still be refunded."""
        return self.amount - self.refunded_amount

    @property
    def is_refundable(self) -> bool:
        """Whether this payment can be (further) refunded."""
        return (
            self.is_successful
            and self.refund_status in (self.RefundStatus.NONE, self.RefundStatus.PARTIAL)
            and self.refundable_amount > Decimal("0.00")
        )


class WebhookDeliveryLog(models.Model):
    """Log of webhook delivery attempts to external services."""

    service = models.ForeignKey(
        ServiceProduct,
        on_delete=models.CASCADE,
        related_name="webhook_logs",
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="webhook_logs",
    )
    url = models.URLField("webhook URL")
    event = models.CharField("event type", max_length=50)

    # Request
    request_headers = models.JSONField("request headers", default=dict)
    request_body = models.JSONField("request body", default=dict)

    # Response
    response_status = models.IntegerField("response status code", null=True, blank=True)
    response_body = models.TextField("response body", blank=True)

    # Delivery info
    attempt = models.IntegerField("attempt number", default=1)
    success = models.BooleanField("successful", default=False)
    error_message = models.TextField("error message", blank=True)
    duration_ms = models.IntegerField("duration (ms)", null=True, blank=True)

    created_at = models.DateTimeField("created", auto_now_add=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]
        verbose_name = "webhook delivery log"
        verbose_name_plural = "webhook delivery logs"

    def __str__(self) -> str:
        status = "ok" if self.success else "failed"
        return f"[{status}] {self.event} → {self.service.name} (attempt {self.attempt})"

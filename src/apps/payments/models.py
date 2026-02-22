"""Payment models for Paystack integration."""

from typing import ClassVar

from django.conf import settings
from django.db import models


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
        return f"{self.reference} - {self.currency} {self.amount} ({self.status})"

    @property
    def amount_in_kobo(self) -> int:
        """Return amount in the smallest currency unit (kobo/cents) for Paystack API."""
        return int(self.amount * 100)

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == self.Status.SUCCESS

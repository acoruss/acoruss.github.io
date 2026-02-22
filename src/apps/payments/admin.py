"""Admin configuration for payments."""

from typing import ClassVar

from django.contrib import admin

from .models import Payment, ServiceProduct, WebhookDeliveryLog


@admin.register(ServiceProduct)
class ServiceProductAdmin(admin.ModelAdmin):
    """Admin view for ServiceProduct model."""

    list_display = ("name", "slug", "is_active", "contact_email", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "slug", "contact_email")
    readonly_fields = ("api_key", "api_secret", "created_at", "updated_at")
    prepopulated_fields: ClassVar[dict] = {"slug": ("name",)}
    ordering = ("-created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin view for Payment model."""

    list_display = (
        "reference",
        "service",
        "email",
        "amount",
        "currency",
        "status",
        "refund_status",
        "created_at",
    )
    list_filter = ("status", "currency", "refund_status", "service", "created_at")
    search_fields = ("reference", "email", "name", "paystack_id", "service_reference")
    readonly_fields = (
        "reference",
        "paystack_id",
        "authorization_url",
        "paystack_refund_id",
        "webhook_delivered",
        "webhook_delivered_at",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("service", "user")


@admin.register(WebhookDeliveryLog)
class WebhookDeliveryLogAdmin(admin.ModelAdmin):
    """Admin view for WebhookDeliveryLog."""

    list_display = ("event", "service", "payment", "attempt", "success", "response_status", "created_at")
    list_filter = ("success", "event", "service", "created_at")
    search_fields = ("url", "event")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

"""Admin configuration for payments."""

from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin view for Payment model."""

    list_display = ("reference", "email", "amount", "currency", "status", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("reference", "email", "name", "paystack_id")
    readonly_fields = ("reference", "paystack_id", "authorization_url", "created_at", "updated_at")
    ordering = ("-created_at",)

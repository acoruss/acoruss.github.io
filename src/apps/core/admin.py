"""Core app admin configuration."""

from django.contrib import admin

from .models import ContactSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    """Admin interface for contact form submissions."""

    list_display = ("name", "email", "company", "project_type", "is_read", "created_at")
    list_filter = ("is_read", "project_type", "created_at")
    search_fields = ("name", "email", "company", "phone", "message")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

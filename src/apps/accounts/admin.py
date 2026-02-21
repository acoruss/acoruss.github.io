"""Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for the custom User model."""

    list_display = ("email", "username", "is_admin", "is_staff", "is_active", "date_joined")
    list_filter = ("is_admin", "is_staff", "is_active")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (*BaseUserAdmin.fieldsets, ("Acoruss", {"fields": ("is_admin",)}))

    add_fieldsets = (*BaseUserAdmin.add_fieldsets, ("Acoruss", {"fields": ("email", "is_admin")}))

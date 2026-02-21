"""Pytest configuration for Acoruss tests."""

import django
from django.conf import settings


def pytest_configure() -> None:
    """Configure Django settings for pytest."""
    settings.DJANGO_SETTINGS_MODULE = "config.settings.test"
    django.setup()

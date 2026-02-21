"""Context processors for the core app."""

from django.conf import settings
from django.http import HttpRequest


def site_context(request: HttpRequest) -> dict:
    """Add site-wide context variables to all templates."""
    return {
        "GOOGLE_ANALYTICS_ID": getattr(settings, "GOOGLE_ANALYTICS_ID", ""),
        "SITE_NAME": "Acoruss",
        "SITE_TAGLINE": "Empowering Businesses Through Technology",
    }

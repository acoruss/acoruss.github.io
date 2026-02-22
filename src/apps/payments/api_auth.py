"""API authentication for service-to-service communication."""

import logging
import time

from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter (per-process)
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 60  # per window


def get_client_ip(request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _check_rate_limit(key: str) -> bool:
    """Return True if the request is within rate limits."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []
    # Prune expired entries
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > window_start]
    if len(_rate_limit_store[key]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    _rate_limit_store[key].append(now)
    return True


class ServiceAuthMixin:
    """
    Mixin for class-based views that require service API key auth.

    Sets ``request.service`` and ``request.client_ip`` on success.
    """

    async def dispatch(self, request, *args, **kwargs):
        """Validate API key before dispatching to the handler."""
        from .models import ServiceProduct

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Missing or invalid Authorization header. Use: Bearer <api_key>"},
                status=401,
            )

        api_key = auth_header[7:]  # Strip "Bearer "

        # Rate limit by truncated key
        if not _check_rate_limit(f"api:{api_key[:12]}"):
            logger.warning("Rate limit exceeded for API key: %s...", api_key[:12])
            return JsonResponse(
                {"error": "Rate limit exceeded. Try again later."},
                status=429,
            )

        try:
            service = await ServiceProduct.objects.aget(api_key=api_key, is_active=True)
        except ServiceProduct.DoesNotExist:
            logger.warning("Invalid API key attempt: %s...", api_key[:12])
            return JsonResponse({"error": "Invalid API key"}, status=401)

        # IP allowlisting
        client_ip = get_client_ip(request)
        if service.allowed_ips and client_ip not in service.allowed_ips:
            logger.warning("IP %s not in allowlist for service %s", client_ip, service.name)
            return JsonResponse({"error": "IP address not allowed"}, status=403)

        request.service = service
        request.client_ip = client_ip

        return await super().dispatch(request, *args, **kwargs)

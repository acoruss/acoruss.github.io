"""
Security middleware to block malicious probe requests.

Bots continuously scan for common vulnerability paths (.env files,
PHP files, WordPress endpoints, config files, path traversal, etc.).
This middleware returns 403 immediately for those paths, avoiding
unnecessary view processing and keeping logs clean.
"""

import logging
import re

from django.http import HttpResponse

logger = logging.getLogger("security.probes")

# Compiled patterns for malicious path probes
_BLOCKED_PATTERNS: re.Pattern[str] = re.compile(
    r"(?i)"
    # Path traversal attempts
    r"(?:\.\./)"
    # .env file variants
    r"|(?:\.env(?:\.\w+)?$)"
    # PHP files
    r"|(?:\.php$)"
    # WordPress / WooCommerce paths
    r"|(?:/wp-(?:admin|content|json|config))"
    # Java/Spring actuator & config endpoints
    r"|(?:/(?:actuator|configprops|manage)/)"
    r"|(?:/actuator$|/configprops$)"
    # Docker / VCS / IDE config files
    r"|(?:/docker-compose\.yml$)"
    r"|(?:/\.git/)"
    r"|(?:/\.vscode/)"
    # Symfony / Laravel debug paths
    r"|(?:/_profiler)"
    r"|(?:/_wdt$)"
    r"|(?:/_ignition/)"
    r"|(?:/telescope/)"
    r"|(?:/horizon/)"
    r"|(?:/app_dev\.php)"
    r"|(?:/__debug__/)"
    # Sensitive config/credential files
    r"|(?:/credentials\.json$)"
    r"|(?:/config\.json$)"
    r"|(?:/config\.js$)"
    r"|(?:/config\.env$)"
    r"|(?:/env\.json$)"
    r"|(?:/env\.js$)"
    r"|(?:/__env\.js$)"
    r"|(?:/\.vite/)"
    r"|(?:/manifest\.json$)"
    r"|(?:/asset-manifest\.json$)"
    # JS source / dev server probes
    r"|(?:/webpack-dev-server$)"
    r"|(?:/__webpack_dev_server__/)"
    r"|(?:/%40vite/client$)"
    r"|(?:/_next/data/)"
    # K8s secrets / GraphQL introspection
    r"|(?:/api/v1/namespaces/)"
    r"|(?:/graphql\?query=\{__schema)"
    # Server status pages
    r"|(?:/server-(?:status|info)$)"
    # Common vuln probe markers
    r"|(?:/__cve_probe)"
    # Checkout / payment / stripe probes (not our URL patterns)
    r"|(?:/(?:checkout|payment|stripe)\.js$)"
    r"|(?:/(?:bundle|vendor|main|index|app|sw|constants)\.js$)"
)


class MaliciousRequestBlockerMiddleware:
    """
    Middleware that blocks known malicious/scanner probe requests
    with a 403 Forbidden response before they reach any view.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if _BLOCKED_PATTERNS.search(path):
            ip = self._get_client_ip(request)
            logger.warning("Blocked malicious probe: %s %s from %s", request.method, path, ip)
            return HttpResponse("Forbidden", status=403, content_type="text/plain")

        return self.get_response(request)

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP, respecting X-Forwarded-For behind a proxy."""
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

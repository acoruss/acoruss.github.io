"""
Security middleware to block malicious probe requests and auto-ban offenders.

Bots continuously scan for common vulnerability paths (.env files,
PHP files, WordPress endpoints, config files, path traversal, etc.).
This middleware:
  1. Blocks known malicious path patterns with a minimal 403.
  2. Immediately bans the IP on the first probe hit (configurable threshold).
  3. Banned IPs get an immediate connection-reset-style empty response.
  4. Catches additional snooping patterns that were slipping through as 404s.
"""

import logging
import re
import threading
import time

from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger("security.probes")

# ---------------------------------------------------------------------------
# Auto-ban configuration (overridable via Django settings)
# ---------------------------------------------------------------------------
# Number of blocked probe hits before an IP is auto-banned (1 = immediate)
PROBE_BAN_THRESHOLD: int = getattr(settings, "PROBE_BAN_THRESHOLD", 1)
# How long (seconds) strike history is kept before resetting
PROBE_STRIKE_WINDOW: int = getattr(settings, "PROBE_STRIKE_WINDOW", 300)  # 5 min
# How long (seconds) a banned IP stays banned
PROBE_BAN_DURATION: int = getattr(settings, "PROBE_BAN_DURATION", 86_400)  # 24 hours

# ---------------------------------------------------------------------------
# In-memory strike counter and ban list (per-process, safe for gunicorn)
# ---------------------------------------------------------------------------
_lock = threading.Lock()
# {ip: [timestamp, timestamp, ...]}
_strike_store: dict[str, list[float]] = {}
# {ip: ban_expiry_timestamp}
_banned_ips: dict[str, float] = {}

# ---------------------------------------------------------------------------
# Permanently blocked IPs (known scanners) — loaded from settings if present
# ---------------------------------------------------------------------------
_PERMANENTLY_BLOCKED_IPS: set[str] = set(getattr(settings, "BLOCKED_IPS", []))

# ---------------------------------------------------------------------------
# Path patterns that are ALWAYS malicious on a Django site
# ---------------------------------------------------------------------------
_BLOCKED_PATH_PATTERNS: re.Pattern[str] = re.compile(
    r"(?i)"
    # ── Path traversal ──
    r"(?:\.\./)"
    # ── .env file variants (any subdir, any suffix) ──
    r"|(?:/\.env(?:\.\w+)*(?:/|$))"
    r"|(?:\.env$)"
    # ── PHP files (anywhere) ──
    r"|(?:\.php[\d]?(?:\.\w+)*$)"
    # ── WordPress / WooCommerce / common CMS ──
    r"|(?:/wp-(?:admin|content|includes|json|config|login|trackback|cron|good))"
    r"|(?:/xmlrpc\.php)"
    r"|(?:/wp-config)"
    # ── Java / Spring ──
    r"|(?:/(?:actuator|configprops|manage)(?:/|$))"
    # ── Git / SVN / Hg / VCS ──
    r"|(?:/\.(?:git|svn|hg|bzr)(?:/|$))"
    # ── IDE / editor config ──
    r"|(?:/\.(?:vscode|idea|c9|vite)(?:/|$))"
    # ── Docker / CI/CD config ──
    r"|(?:/docker-compose\.yml$)"
    r"|(?:/\.docker(?:/|$))"
    r"|(?:/\.circleci(?:/|$))"
    r"|(?:/\.gitlab(?:-ci)?(?:/|$))"
    r"|(?:/\.github(?:/|$))"
    r"|(?:/\.bitbucket(?:/|$))"
    # ── Symfony / Laravel / Rails debug ──
    r"|(?:/_profiler)"
    r"|(?:/_wdt$)"
    r"|(?:/_ignition/)"
    r"|(?:/telescope/)"
    r"|(?:/horizon/)"
    r"|(?:/app_dev\.php)"
    # ── Sensitive credential / config files ──
    r"|(?:/\.aws(?:/|$))"
    r"|(?:/\.ssh(?:/|$))"
    r"|(?:/credentials(?:\.json|\.txt|\.yml|\.yaml)?$)"
    r"|(?:/config\.(?:json|js|env|ini|yml|yaml|php)$)"
    r"|(?:/settings\.(?:json|js|php|ini|py)$)"
    r"|(?:/database\.(?:yml|json|sql)$)"
    r"|(?:/secrets\.(?:json|yml|yaml)$)"
    r"|(?:/env\.(?:json|js|php)$)"
    r"|(?:/api_keys\.json$)"
    r"|(?:/keys\.(?:json|yml)$)"
    r"|(?:/sendgrid\.(?:json|env)$)"
    r"|(?:/aws(?:-secret)?\.(?:json|yml|yaml|txt)$)"
    r"|(?:/gcloud\.json$)"
    r"|(?:/firebase\.json$)"
    r"|(?:/manifest\.json$)"
    r"|(?:/now\.json$)"
    # ── Backup / dump / log files ──
    r"|(?:\.(?:sql|bak|backup|old|save|swp|orig)$)"
    r"|(?:/(?:dump|backup|db_backup)\.(?:sql|sh|tar\.gz|zip)$)"
    r"|(?:/(?:error|debug|access|server|app)\.log$)"
    r"|(?:/storage/logs/)"
    r"|(?:/logs/(?:error|access|app)\.log$)"
    # ── Server info / status ──
    r"|(?:/server-(?:status|info)$)"
    # ── CGI / admin panels ──
    r"|(?:/cgi-bin/)"
    r"|(?:/phpmyadmin)"
    r"|(?:/phpMyAdmin)"
    r"|(?:/adminer)"
    r"|(?:/db-admin/)"
    # ── Webpack / Vite / Next.js dev server probes ──
    r"|(?:/webpack-dev-server)"
    r"|(?:/__webpack_dev_server__/)"
    r"|(?:/%40vite/client)"
    r"|(?:/_next/(?:data|static)/)"
    r"|(?:/_astro/)"
    # ── Misc probes ──
    r"|(?:/graphql\?query=\{__schema)"
    r"|(?:/api/v1/namespaces/)"
    r"|(?:/__cve_probe)"
    r"|(?:/robots/)"  # /robots/ dir (not /robots.txt)
    r"|(?:/uploads/)"
    r"|(?:/wp-includes/)"
    r"|(?:\.well-known/$)"  # the dir listing, not valid .well-known paths
    # ── Common .js probes (source maps, bundled files) ──
    r"|(?:/(?:bundle|vendor|main|index|app|sw|constants|src/app|lib/config)\.js$)"
    r"|(?:/(?:checkout|payment|stripe)\.js$)"
    r"|(?:/service-worker\.js$)"
    # ── Config / secret YAML/TOML/env files ──
    r"|(?:/(?:serverless|docker-compose|app|main)\.yml$)"
    r"|(?:/(?:config|secrets)/.*\.(?:yml|yaml|json)$)"
    r"|(?:/(?:Procfile|Makefile|netlify\.toml)$)"
    r"|(?:/(?:composer\.lock|package\.json|rollup\.config\.js)$)"
    # ── Private key files ──
    r"|(?:/(?:private|server)\.key$)"
    # ── Dotfiles ──
    r"|(?:/\.(?:npmrc|pypirc|htaccess|gitignore|travis\.yml|dockerignore|flaskenv)$)"
    r"|(?:/\.(?:envrc|rbenv|jenv|hsenv|powenv|zshenv))"
    r"|(?:/\.(?:boto|local|remote|production)$)"
)

# Suspicious user-agent fragments (known vulnerability scanners)
_SUSPICIOUS_UA_PATTERNS: re.Pattern[str] = re.compile(
    r"(?i)"
    r"(?:nikto|sqlmap|nmap|masscan|nessus|openvas|dirbuster|gobuster)"
    r"|(?:wpscan|joomscan|acunetix|burpsuite|nuclei|zgrab)"
    r"|(?:python-requests/|python-urllib|libwww-perl|curl/|wget/)"
    r"|(?:Go-http-client|fasthttp|httpx|PycURL)"
)


def _get_client_ip(request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _record_strike(ip: str) -> bool:
    """
    Record a probe strike for an IP.

    Returns True if the IP should be banned (threshold reached).
    """
    now = time.monotonic()
    window_start = now - PROBE_STRIKE_WINDOW

    with _lock:
        strikes = _strike_store.get(ip, [])
        # Prune old strikes
        strikes = [t for t in strikes if t > window_start]
        strikes.append(now)
        _strike_store[ip] = strikes

        if len(strikes) >= PROBE_BAN_THRESHOLD:
            _banned_ips[ip] = now + PROBE_BAN_DURATION
            # Clean up strikes — no longer needed
            _strike_store.pop(ip, None)
            return True
    return False


def _is_banned(ip: str) -> bool:
    """Check if an IP is currently banned."""
    if ip in _PERMANENTLY_BLOCKED_IPS:
        return True

    with _lock:
        expiry = _banned_ips.get(ip)
        if expiry is None:
            return False
        if time.monotonic() > expiry:
            # Ban expired — clean up
            _banned_ips.pop(ip, None)
            return False
        return True


def _cleanup_expired() -> None:
    """Periodically clean up expired bans and old strikes (called occasionally)."""
    now = time.monotonic()
    with _lock:
        expired_bans = [ip for ip, exp in _banned_ips.items() if now > exp]
        for ip in expired_bans:
            del _banned_ips[ip]

        window_start = now - PROBE_STRIKE_WINDOW
        expired_strikes = [ip for ip, ts in _strike_store.items() if all(t < window_start for t in ts)]
        for ip in expired_strikes:
            del _strike_store[ip]


# Counter for periodic cleanup (every ~100 requests)
_request_counter = 0
_CLEANUP_INTERVAL = 100


class MaliciousRequestBlockerMiddleware:
    """
    Middleware that blocks known malicious/scanner probe requests,
    auto-bans repeat offender IPs, and returns minimal responses
    to waste as few server resources as possible.
    """

    # Minimal empty response — no body, no useful headers
    BLOCKED_RESPONSE = HttpResponse(status=403)
    BLOCKED_RESPONSE["Content-Length"] = "0"
    BLOCKED_RESPONSE["Connection"] = "close"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _request_counter

        ip = _get_client_ip(request)

        # Skip security checks for loopback/internal IPs (health checks, reverse proxy)
        if ip in ("127.0.0.1", "::1", "localhost"):
            return self.get_response(request)

        # Fast path: already banned IP — drop immediately
        if _is_banned(ip):
            return self._drop(request, ip, reason="banned")

        path = request.path

        # Check path against blocked patterns
        if _BLOCKED_PATH_PATTERNS.search(path):
            was_banned = _record_strike(ip)
            if was_banned:
                logger.warning("Auto-banned IP %s after %d probe strikes", ip, PROBE_BAN_THRESHOLD)
            else:
                logger.info("Blocked probe: %s %s from %s", request.method, path, ip)
            return self._drop(request, ip, reason="probe")

        # Check suspicious User-Agent (only for non-API paths)
        if not path.startswith("/api/"):
            ua = request.META.get("HTTP_USER_AGENT", "")
            if ua and _SUSPICIOUS_UA_PATTERNS.search(ua):
                _record_strike(ip)
                logger.info("Blocked suspicious UA: %s from %s (path: %s)", ua[:80], ip, path)
                return self._drop(request, ip, reason="suspicious-ua")

        # Periodic cleanup of expired data
        _request_counter += 1
        if _request_counter >= _CLEANUP_INTERVAL:
            _request_counter = 0
            _cleanup_expired()

        return self.get_response(request)

    def _drop(self, request, ip: str, *, reason: str) -> HttpResponse:
        """Return a minimal 403 with Connection: close."""
        return HttpResponse(status=403, headers={"Connection": "close", "Content-Length": "0"})

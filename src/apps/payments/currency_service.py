"""
Currency conversion service using the Open Exchange Rates API.

Uses https://open.er-api.com/v6/latest/{base} — free, no API key,
backed by IMF / central-bank data, supports 150+ currencies including KES.

Exchange rates are cached in-memory for 1 hour (configurable via
settings.EXCHANGE_RATE_CACHE_TTL) to minimise external API calls.
"""

import asyncio
import json
import logging
import threading
import time
from datetime import UTC
from decimal import ROUND_HALF_UP, Decimal
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest"
SETTLEMENT_CURRENCY = "KES"
CACHE_TTL: int = getattr(settings, "EXCHANGE_RATE_CACHE_TTL", 3600)  # 1 hour

# ---------------------------------------------------------------------------
# In-memory rate cache: { "USD": { "KES": 129.50, ... }, _fetched: float }
# ---------------------------------------------------------------------------
_cache_lock = threading.Lock()
_rate_cache: dict[str, dict] = {}


def _cache_key(base: str) -> str:
    return base.upper()


def _get_cached_rates(base: str) -> dict | None:
    """Return cached rates for *base* if still fresh, else None."""
    key = _cache_key(base)
    with _cache_lock:
        entry = _rate_cache.get(key)
        if entry and (time.monotonic() - entry["_fetched"]) < CACHE_TTL:
            return entry
    return None


def _store_rates(base: str, rates: dict) -> None:
    """Store rates in the in-memory cache."""
    key = _cache_key(base)
    with _cache_lock:
        _rate_cache[key] = {**rates, "_fetched": time.monotonic()}


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------
def _fetch_rates_sync(base: str) -> dict:
    """
    Fetch exchange rates from the API (synchronous, for executor use).

    Returns the full rates dict: {"USD": 1.0, "KES": 129.50, ...}
    Raises RuntimeError on failure.
    """
    url = f"{EXCHANGE_RATE_API_URL}/{base.upper()}"
    req = Request(url, headers={"Accept": "application/json"})  # noqa: S310

    try:
        resp = urlopen(req, timeout=10)  # noqa: S310
        data = json.loads(resp.read())
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")[:300]
        msg = f"Exchange rate API returned HTTP {exc.code}: {body}"
        logger.error(msg)
        raise RuntimeError(msg) from exc
    except Exception as exc:
        msg = f"Exchange rate API request failed: {exc}"
        logger.error(msg)
        raise RuntimeError(msg) from exc

    if data.get("result") != "success":
        msg = f"Exchange rate API error: {data}"
        logger.error(msg)
        raise RuntimeError(msg)

    rates = data.get("rates")
    if not rates or SETTLEMENT_CURRENCY not in rates:
        msg = f"Exchange rate API did not return {SETTLEMENT_CURRENCY} rate"
        logger.error(msg)
        raise RuntimeError(msg)

    return rates


async def get_exchange_rate(from_currency: str, to_currency: str = SETTLEMENT_CURRENCY) -> Decimal:
    """
    Get the exchange rate from *from_currency* to *to_currency*.

    Uses an in-memory cache with a configurable TTL.
    Falls back to a live API call when the cache is stale.

    Returns:
        The exchange rate as a Decimal (e.g. 129.50 for USD→KES).

    Raises:
        RuntimeError: If the rate cannot be fetched.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    # Same currency — rate is 1
    if from_currency == to_currency:
        return Decimal("1")

    cached = _get_cached_rates(from_currency)
    if cached and to_currency in cached:
        return Decimal(str(cached[to_currency]))

    # Fetch fresh rates in an executor (async-safe)
    loop = asyncio.get_event_loop()
    rates = await loop.run_in_executor(None, _fetch_rates_sync, from_currency)
    _store_rates(from_currency, rates)

    rate = rates.get(to_currency)
    if rate is None:
        msg = f"No exchange rate found for {from_currency} → {to_currency}"
        raise RuntimeError(msg)

    return Decimal(str(rate))


async def convert_to_kes(
    amount: Decimal,
    from_currency: str,
) -> dict:
    """
    Convert *amount* from *from_currency* to KES.

    Returns a dict with all conversion details suitable for metadata:
        {
            "original_amount": "25.00",
            "original_currency": "USD",
            "exchange_rate": "129.50",
            "converted_amount": "3237.50",
            "settlement_currency": "KES",
            "rate_source": "open.er-api.com",
            "rate_timestamp": "2026-02-23T12:00:00Z",
        }
    """
    from datetime import datetime

    from_currency = from_currency.upper()

    if from_currency == SETTLEMENT_CURRENCY:
        return {
            "original_amount": str(amount),
            "original_currency": from_currency,
            "exchange_rate": "1",
            "converted_amount": str(amount),
            "settlement_currency": SETTLEMENT_CURRENCY,
            "conversion_applied": False,
            "rate_source": "identity",
            "rate_timestamp": datetime.now(UTC).isoformat(),
        }

    rate = await get_exchange_rate(from_currency, SETTLEMENT_CURRENCY)
    converted = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "original_amount": str(amount),
        "original_currency": from_currency,
        "exchange_rate": str(rate),
        "converted_amount": str(converted),
        "settlement_currency": SETTLEMENT_CURRENCY,
        "conversion_applied": True,
        "rate_source": "open.er-api.com",
        "rate_timestamp": datetime.now(UTC).isoformat(),
    }

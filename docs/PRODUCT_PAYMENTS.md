# Acoruss Payment Platform — Service Integration Guide

This document explains how an external service (e.g. **xperience-nairobi**) integrates with the Acoruss centralized payment platform.

> **Base URL (production):** `https://acoruss.com`
> **Base URL (development):** `http://localhost:8083`

---

## Table of Contents

1. [Overview](#overview)
2. [Onboarding](#onboarding)
3. [Authentication](#authentication)
4. [API Reference](#api-reference)
   - [Initiate Payment](#1-initiate-payment)
   - [Get Payment Status](#2-get-payment-status)
   - [List Payments](#3-list-payments)
   - [Request Refund](#4-request-refund)
5. [Webhooks](#webhooks)
   - [Receiving Webhooks](#receiving-webhooks)
   - [Verifying Signatures](#verifying-signatures)
   - [Webhook Events](#webhook-events)
   - [Retry Policy](#retry-policy)
6. [Payment Flow](#payment-flow)
7. [Callback Redirects](#callback-redirects)
8. [Idempotency](#idempotency)
9. [Currencies](#currencies)
10. [Rate Limits](#rate-limits)
11. [Error Handling](#error-handling)
12. [Example: xperience-nairobi Integration](#example-xperience-nairobi-integration)

---

## Overview

Acoruss acts as a payment gateway proxy over Paystack. Your service calls the Acoruss API to initiate payments — Acoruss handles the Paystack integration, webhook processing, and notifies your service when a payment succeeds, fails, or is refunded.

```
┌─────────────┐     ┌─────────────┐     ┌──────────┐     ┌──────────┐
│  Your App   │────▶│   Acoruss   │────▶│ Paystack │────▶│ Customer │
│ (xperience) │◀────│   API       │◀────│          │◀────│ (pays)   │
└─────────────┘     └─────────────┘     └──────────┘     └──────────┘
   webhook ◀──────── notification
```

**Why use Acoruss instead of Paystack directly?**

- Centralised billing, reporting, and refund management across all Acoruss products
- Per-service credential isolation and IP allowlisting
- Dashboard visibility for the Acoruss team
- Automatic webhook delivery with retries

---

## Onboarding

An Acoruss admin registers your service at `/dashboard/services/create/`. You'll receive:

| Credential     | Format               | Purpose                            |
| -------------- | -------------------- | ---------------------------------- |
| **API Key**    | `ak_` + 48 hex chars | Authenticate API requests          |
| **API Secret** | `sk_` + 64 hex chars | Verify incoming webhook signatures |

Store both securely. The **API Key** is sent with every API request. The **API Secret** is only used server-side to verify webhook signatures — never send it in requests.

The admin also configures:

- **Webhook URL** — where Acoruss POSTs payment events to your service
- **Default Callback URL** — where users redirect after payment (can be overridden per request)
- **Allowed Currencies** — optional restriction (empty = all supported)
- **Allowed IPs** — optional API call restriction (empty = all)

---

## Authentication

All API requests require a `Bearer` token in the `Authorization` header:

```
Authorization: Bearer ak_your_api_key_here
```

**Errors:**

| Status | Meaning                                     |
| ------ | ------------------------------------------- |
| `401`  | Missing/invalid key, or service is disabled |
| `403`  | IP not in allowlist                         |
| `429`  | Rate limit exceeded (60 req/min)            |

---

## API Reference

### 1. Initiate Payment

**`POST /api/v1/payments/initiate/`**

Start a payment. Returns a Paystack authorization URL to redirect the customer to.

**Request:**

```json
{
  "email": "customer@example.com",
  "amount": 2500,
  "currency": "KES",
  "name": "Jane Doe",
  "description": "VIP Ticket — Xperience Nairobi 2026",
  "service_reference": "order-xp-00123",
  "callback_url": "https://xperience-nairobi.com/payment/done/",
  "metadata": {
    "ticket_type": "vip",
    "event_id": "xp-2026-feb"
  },
  "idempotency_key": "order-xp-00123-pay-1"
}
```

| Field               | Type   | Required | Description                                                   |
| ------------------- | ------ | -------- | ------------------------------------------------------------- |
| `email`             | string | **Yes**  | Customer email                                                |
| `amount`            | number | **Yes**  | Amount in major currency unit (e.g. 2500 = KES 2,500)         |
| `currency`          | string | No       | Any supported currency code (default: `KES`). See [Currencies](#currencies). Amounts are auto-converted to KES for settlement. |
| `name`              | string | No       | Customer name                                                 |
| `description`       | string | No       | Payment description                                           |
| `service_reference` | string | No       | Your internal order/transaction ID                            |
| `callback_url`      | string | No       | Override the default redirect URL for this payment            |
| `metadata`          | object | No       | Arbitrary key/value data (returned in webhooks)               |
| `idempotency_key`   | string | No       | Prevents duplicate payments (see [Idempotency](#idempotency)) |

**Response (200):**

```json
{
  "status": true,
  "message": "Payment initiated",
  "data": {
    "reference": "acoruss-a1b2c3d4e5f6",
    "authorization_url": "https://checkout.paystack.com/abc123",
    "callback_url": "https://xperience-nairobi.com/payment/done/",
    "currency_conversion": {
      "original_amount": "25.00",
      "original_currency": "USD",
      "settlement_amount": "3237.50",
      "settlement_currency": "KES",
      "exchange_rate": "129.50"
    }
  }
}
```

> **Note:** The `currency_conversion` field is only included when the original currency is not KES.

**Next step:** Redirect the customer's browser to `authorization_url`. After payment, they'll be redirected to your `callback_url` with query parameters (see [Callback Redirects](#callback-redirects)).

---

### 2. Get Payment Status

**`GET /api/v1/payments/{reference}/`**

Check the current status of a payment.

**Response (200):**

```json
{
  "status": true,
  "data": {
    "reference": "acoruss-a1b2c3d4e5f6",
    "service_reference": "order-xp-00123",
    "email": "customer@example.com",
    "name": "Jane Doe",
    "amount": "2500.00",
    "currency": "KES",
    "description": "VIP Ticket — Xperience Nairobi 2026",
    "status": "success",
    "channel": "card",
    "fees": "62.50",
    "net_amount": "2437.50",
    "refund_status": "none",
    "refunded_amount": "0.00",
    "created_at": "2026-02-22T14:30:00+03:00",
    "updated_at": "2026-02-22T14:31:15+03:00"
  }
}
```

**Payment statuses:** `pending`, `success`, `failed`, `abandoned`

---

### 3. List Payments

**`GET /api/v1/payments/`**

Paginated list of your service's payments. Only returns payments belonging to your service.

**Query parameters:**

| Param      | Type   | Default | Description                                         |
| ---------- | ------ | ------- | --------------------------------------------------- |
| `status`   | string | —       | Filter: `pending`, `success`, `failed`, `abandoned` |
| `email`    | string | —       | Filter by customer email                            |
| `page`     | int    | 1       | Page number                                         |
| `per_page` | int    | 20      | Results per page (max 100)                          |

**Response (200):**

```json
{
  "status": true,
  "data": [
    {
      "reference": "acoruss-a1b2c3d4e5f6",
      "service_reference": "order-xp-00123",
      "email": "customer@example.com",
      "amount": "2500.00",
      "currency": "KES",
      "status": "success",
      "refund_status": "none",
      "created_at": "2026-02-22T14:30:00+03:00"
    }
  ],
  "meta": {
    "total": 42,
    "page": 1,
    "per_page": 20,
    "pages": 3
  }
}
```

---

### 4. Request Refund

**`POST /api/v1/payments/{reference}/refund/`**

Initiate a full or partial refund for a successful payment.

**Request (partial refund):**

```json
{
  "amount": 500,
  "reason": "Customer cancelled one ticket"
}
```

**Request (full refund):** Send an empty body or `{}`.

| Field    | Type   | Required | Description                                 |
| -------- | ------ | -------- | ------------------------------------------- |
| `amount` | number | No       | Partial refund amount. Omit for full refund |
| `reason` | string | No       | Customer-facing refund reason               |

**Response (200):**

```json
{
  "status": true,
  "message": "Refund initiated",
  "data": {
    "reference": "acoruss-a1b2c3d4e5f6",
    "refund_status": "partial",
    "refunded_amount": "500.00",
    "refundable_amount": "2000.00"
  }
}
```

**Refund statuses:** `none`, `pending`, `partial`, `full`, `failed`

---

## Webhooks

### Receiving Webhooks

When a payment event occurs, Acoruss POSTs a JSON payload to your configured **Webhook URL**.

```
POST https://your-service.com/webhook/acoruss/
Content-Type: application/json
X-Acoruss-Signature: <hmac-sha256-hex>
X-Acoruss-Event: payment.success
User-Agent: Acoruss-Payments/1.0
```

### Verifying Signatures

**Always verify the signature** before processing a webhook. The `X-Acoruss-Signature` header contains an HMAC-SHA256 hex digest of the raw request body, signed with your **API Secret**.

**Python:**

```python
import hashlib
import hmac

def verify_acoruss_webhook(request_body: bytes, signature: str, api_secret: str) -> bool:
    expected = hmac.new(
        api_secret.encode(),
        request_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

**Node.js:**

```javascript
const crypto = require("crypto");

function verifyAcorussWebhook(body, signature, apiSecret) {
  const expected = crypto
    .createHmac("sha256", apiSecret)
    .update(body)
    .digest("hex");
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(signature));
}
```

### Webhook Events

| Event              | When it fires                 |
| ------------------ | ----------------------------- |
| `payment.success`  | Payment confirmed by Paystack |
| `payment.refunded` | Refund processed              |

**Webhook payload:**

```json
{
  "event": "payment.success",
  "data": {
    "reference": "acoruss-a1b2c3d4e5f6",
    "service_reference": "order-xp-00123",
    "email": "customer@example.com",
    "name": "Jane Doe",
    "amount": "2500.00",
    "currency": "KES",
    "status": "success",
    "channel": "card",
    "fees": "62.50",
    "description": "VIP Ticket — Xperience Nairobi 2026",
    "refund_status": "none",
    "refunded_amount": "0.00",
    "metadata": {
      "ticket_type": "vip",
      "event_id": "xp-2026-feb"
    },
    "created_at": "2026-02-22T14:30:00+03:00"
  }
}
```

### Retry Policy

If your webhook endpoint returns a non-2xx status or is unreachable, Acoruss retries up to **3 times** with increasing delays:

| Attempt | Delay      |
| ------- | ---------- |
| 1       | Immediate  |
| 2       | +1 second  |
| 3       | +5 seconds |

All delivery attempts are logged and visible in the Acoruss dashboard.

**Your webhook endpoint should:**

- Respond with `2xx` within 15 seconds
- Be idempotent (you may receive the same event more than once)
- Verify the `X-Acoruss-Signature` before processing

---

## Payment Flow

Here's the complete lifecycle for a typical payment:

```
1. Your server ──POST /api/v1/payments/initiate/──▶ Acoruss API
                                                      │
2.              ◀── { authorization_url } ─────────────┘

3. Your frontend ── redirect customer to authorization_url ──▶ Paystack Checkout
                                                                    │
4. Customer pays on Paystack                                        │
                                                                    │
5.              Paystack ──webhook──▶ Acoruss (processes payment)   │
                                         │                         │
6.              Acoruss  ──webhook──▶ Your Server (payment.success) │
                                                                    │
7. Paystack ── redirect customer ──▶ Acoruss /payments/verify/      │
                                         │
8. Acoruss  ── redirect customer ──▶ Your callback_url?reference=...&status=success
```

**Important:** Don't rely solely on the callback redirect (step 8) to confirm payment — use the webhook (step 6) or poll the status API as the source of truth.

---

## Callback Redirects

After payment, the customer is redirected to your `callback_url` with these query parameters:

```
https://xperience-nairobi.com/payment/done/?reference=acoruss-a1b2c3d4e5f6&status=success
```

| Param       | Description                                      |
| ----------- | ------------------------------------------------ |
| `reference` | The Acoruss payment reference                    |
| `status`    | Payment status: `success`, `failed`, `abandoned` |

**Do not trust the `status` query parameter alone.** Always verify via the webhook or the [Get Payment Status](#2-get-payment-status) API.

---

## Idempotency

To prevent duplicate payments (e.g. user double-clicks, network retries), include an `idempotency_key` in your initiate request.

- If a payment with the same `idempotency_key` already exists for your service, the existing payment is returned without calling Paystack again.
- Use your own order ID or a generated UUID as the key.
- Keys are scoped per-service — two services can use the same key independently.

```json
{
  "email": "customer@example.com",
  "amount": 2500,
  "idempotency_key": "order-xp-00123-attempt-1"
}
```

---

## Currencies

Accepted currencies (payments are always settled in KES via Paystack):

| Code  | Name                       |
| ----- | -------------------------- |
| `KES` | Kenyan Shilling (default)  |
| `USD` | US Dollar                  |
| `EUR` | Euro                       |
| `GBP` | British Pound              |
| `NGN` | Nigerian Naira             |
| `GHS` | Ghanaian Cedi              |
| `ZAR` | South African Rand         |
| `UGX` | Ugandan Shilling           |
| `TZS` | Tanzanian Shilling         |
| `RWF` | Rwandan Franc              |
| `CAD` | Canadian Dollar            |
| `AUD` | Australian Dollar          |
| `INR` | Indian Rupee               |
| `JPY` | Japanese Yen               |
| `CNY` | Chinese Yuan               |
| `AED` | UAE Dirham                 |
| `CHF` | Swiss Franc                |
| `SGD` | Singapore Dollar           |
| `HKD` | Hong Kong Dollar           |
| `BRL` | Brazilian Real             |
| `MXN` | Mexican Peso               |
| `ETB` | Ethiopian Birr             |
| `EGP` | Egyptian Pound             |
| `ZMW` | Zambian Kwacha             |
| … and more                          |

If your service has an `allowed_currencies` restriction configured, only those currencies will be accepted.

### Currency Conversion

All payments are processed through Paystack in **KES**. When a client submits a payment in a non-KES currency:

1. Acoruss fetches the current exchange rate from the [Open Exchange Rates API](https://open.er-api.com/) (IMF/central-bank data, free, no API key).
2. The amount is converted to KES using the live rate.
3. The KES amount is sent to Paystack for processing.
4. The original amount, currency, exchange rate, and converted amount are stored in the payment metadata.

Exchange rates are cached for **1 hour** (configurable via `EXCHANGE_RATE_CACHE_TTL` setting).

**Example:** A $25 USD payment at a rate of 129.50 KES/USD becomes KES 3,237.50 for Paystack.

The conversion details appear in:
- The **initiate payment** response (`currency_conversion` field)
- The **payment status** response (`settlement` field)
- The **webhook payload** (`metadata.currency_conversion`)
- The **payment list** response (`settlement_amount_kes`, `exchange_rate` fields)

---

## Rate Limits

- **60 requests per minute** per API key
- Returns `429 Too Many Requests` when exceeded

---

## Error Handling

All error responses follow this format:

```json
{
  "error": "Human-readable error message",
  "details": {
    "field_name": "Validation error for this field"
  }
}
```

| Status | Meaning                              |
| ------ | ------------------------------------ |
| `400`  | Validation error (check `details`)   |
| `401`  | Authentication failed                |
| `403`  | IP not allowed                       |
| `404`  | Payment not found (or not yours)     |
| `429`  | Rate limit exceeded                  |
| `502`  | Paystack gateway error (retry later) |

---

## Example: xperience-nairobi Integration

Here's what **xperience-nairobi** needs to implement:

### 1. Environment Variables

```env
ACORUSS_API_URL=https://acoruss.com
ACORUSS_API_KEY=ak_...   # provided by Acoruss admin
ACORUSS_API_SECRET=sk_... # provided by Acoruss admin (for webhook verification only)
```

### 2. Initiate Payment (Server-Side)

```python
import httpx  # or requests, aiohttp, etc.

async def create_payment(order):
    """Call Acoruss to initiate a payment for an order."""
    response = await httpx.AsyncClient().post(
        f"{settings.ACORUSS_API_URL}/api/v1/payments/initiate/",
        json={
            "email": order.customer_email,
            "name": order.customer_name,
            "amount": float(order.total),
            "currency": "KES",
            "description": f"Ticket — {order.event.name}",
            "service_reference": str(order.id),
            "callback_url": f"https://xperience-nairobi.com/orders/{order.id}/paid/",
            "idempotency_key": f"order-{order.id}",
            "metadata": {
                "event_id": str(order.event.id),
                "ticket_type": order.ticket_type,
            },
        },
        headers={"Authorization": f"Bearer {settings.ACORUSS_API_KEY}"},
        timeout=30,
    )
    data = response.json()
    if data.get("status"):
        order.payment_reference = data["data"]["reference"]
        await order.asave(update_fields=["payment_reference"])
        return data["data"]["authorization_url"]  # redirect customer here
    raise PaymentError(data.get("message", "Payment initiation failed"))
```

### 3. Handle Callback Redirect

```python
# GET /orders/<id>/paid/?reference=acoruss-...&status=success
async def payment_callback(request, order_id):
    reference = request.GET.get("reference")
    status = request.GET.get("status")

    if status == "success":
        # Show a "thank you" page — but don't fulfill the order yet!
        # Wait for the webhook for authoritative confirmation.
        return render(request, "payment_pending.html", {"order_id": order_id})
    else:
        return render(request, "payment_failed.html", {"order_id": order_id})
```

### 4. Webhook Endpoint

```python
import hashlib
import hmac
import json

# POST /webhooks/acoruss/
async def acoruss_webhook(request):
    # 1. Verify signature
    signature = request.headers.get("X-Acoruss-Signature", "")
    expected = hmac.new(
        settings.ACORUSS_API_SECRET.encode(),
        request.body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return JsonResponse({"error": "Invalid signature"}, status=400)

    # 2. Parse event
    payload = json.loads(request.body)
    event = payload["event"]
    data = payload["data"]

    if event == "payment.success":
        order = await Order.objects.aget(
            payment_reference=data["reference"]
        )
        order.payment_status = "paid"
        order.payment_channel = data["channel"]
        order.payment_fees = data["fees"]
        await order.asave()

        # Fulfill the order (send tickets, etc.)
        await send_tickets(order)

    elif event == "payment.refunded":
        order = await Order.objects.aget(
            payment_reference=data["reference"]
        )
        order.payment_status = "refunded"
        order.refund_amount = data["refunded_amount"]
        await order.asave()

        await notify_customer_refund(order)

    return JsonResponse({"status": "ok"})
```

### 5. Check Payment Status (Optional Polling)

```python
async def check_payment(reference: str) -> dict:
    """Poll Acoruss for payment status (use as fallback, prefer webhooks)."""
    response = await httpx.AsyncClient().get(
        f"{settings.ACORUSS_API_URL}/api/v1/payments/{reference}/",
        headers={"Authorization": f"Bearer {settings.ACORUSS_API_KEY}"},
        timeout=15,
    )
    return response.json()
```

### Summary of Changes for xperience-nairobi

| What                  | Where                         | Details                                                                        |
| --------------------- | ----------------------------- | ------------------------------------------------------------------------------ |
| **Add env vars**      | `.env` / settings             | `ACORUSS_API_KEY`, `ACORUSS_API_SECRET`, `ACORUSS_API_URL`                     |
| **Initiate endpoint** | Server (checkout flow)        | POST to `/api/v1/payments/initiate/`, redirect customer to `authorization_url` |
| **Callback page**     | Frontend route                | Handle redirect from `?reference=...&status=...`, show pending/success/fail UI |
| **Webhook endpoint**  | Server (`/webhooks/acoruss/`) | Verify signature, process `payment.success` / `payment.refunded` events        |
| **Store reference**   | Order model                   | Save the `acoruss-...` reference for lookups                                   |
| **No Paystack SDK**   | Remove if present             | Acoruss handles all Paystack communication                                     |

**Tell the Acoruss admin** your:

- Webhook URL (e.g. `https://xperience-nairobi.com/webhooks/acoruss/`)
- Callback URL (e.g. `https://xperience-nairobi.com/orders/{id}/paid/`)
- Required currencies (e.g. `KES` only)
- Server IPs if you want IP allowlisting

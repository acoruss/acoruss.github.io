"""Unit tests for the payments application."""

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from django.test import AsyncClient, Client
from django.urls import reverse

from apps.payments.models import (
    Payment,
    ServiceProduct,
    WebhookDeliveryLog,
    generate_api_key,
    generate_api_secret,
)
from apps.payments.services import (
    generate_reference,
    validate_webhook_signature,
)
from apps.payments.webhook_dispatcher import sign_payload

# ─────────────────────────────── Fixtures ────────────────────────────────────


@pytest.fixture
def service(db) -> ServiceProduct:
    """Create a test service product."""
    return ServiceProduct.objects.create(
        name="Test Service",
        slug="test-service",
        description="A test service",
        webhook_url="https://example.com/webhook/",
        default_callback_url="https://example.com/callback/",
        contact_email="test@example.com",
    )


@pytest.fixture
def inactive_service(db) -> ServiceProduct:
    """Create an inactive service product."""
    return ServiceProduct.objects.create(
        name="Inactive Service",
        slug="inactive-service",
        is_active=False,
    )


@pytest.fixture
def payment(db, service: ServiceProduct) -> Payment:
    """Create a test payment."""
    return Payment.objects.create(
        service=service,
        email="customer@example.com",
        name="Test Customer",
        amount=Decimal("1000.00"),
        currency="KES",
        description="Test payment",
        reference="acoruss-test12345",
        status=Payment.Status.SUCCESS,
        fees=Decimal("25.00"),
        channel="card",
        service_reference="order-001",
    )


@pytest.fixture
def pending_payment(db, service: ServiceProduct) -> Payment:
    """Create a pending payment."""
    return Payment.objects.create(
        service=service,
        email="pending@example.com",
        name="Pending Customer",
        amount=Decimal("500.00"),
        currency="KES",
        reference="acoruss-pending123",
        status=Payment.Status.PENDING,
    )


@pytest.fixture
def direct_payment(db) -> Payment:
    """Create a payment without a service (direct)."""
    return Payment.objects.create(
        email="direct@example.com",
        name="Direct Customer",
        amount=Decimal("250.00"),
        currency="USD",
        reference="acoruss-direct123",
        status=Payment.Status.SUCCESS,
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    from apps.accounts.models import User

    return User.objects.create_user(
        username="testadmin",
        email="admin@acoruss.com",
        password="testpass123",
        is_staff=True,
    )


@pytest.fixture
def admin_client(admin_user) -> Client:
    """Return a client logged in as admin."""
    client = Client()
    client.login(username="testadmin", password="testpass123")
    return client


@pytest.fixture
def async_admin_client(admin_user) -> AsyncClient:
    """Return an async client logged in as admin."""
    client = AsyncClient()
    client.login(username="testadmin", password="testpass123")
    return client


# ─────────────────── Model Tests: ServiceProduct ─────────────────────────────


@pytest.mark.django_db
class TestServiceProductModel:
    """Tests for the ServiceProduct model."""

    def test_create_service_generates_credentials(self, service: ServiceProduct) -> None:
        """Service creation auto-generates API key and secret."""
        assert service.api_key.startswith("ak_")
        assert service.api_secret.startswith("sk_")
        assert len(service.api_key) == 51  # ak_ + 48 hex chars
        assert len(service.api_secret) == 67  # sk_ + 64 hex chars

    def test_auto_slug_from_name(self, db) -> None:
        """Slug is auto-generated from name if not provided."""
        svc = ServiceProduct.objects.create(name="My Cool Service")
        assert svc.slug == "my-cool-service"

    def test_explicit_slug_preserved(self, db) -> None:
        """Explicit slug is preserved, not overwritten."""
        svc = ServiceProduct.objects.create(name="A Service", slug="custom-slug")
        assert svc.slug == "custom-slug"

    def test_regenerate_credentials(self, service: ServiceProduct) -> None:
        """Regenerating credentials produces new values."""
        old_key = service.api_key
        old_secret = service.api_secret
        new_key, new_secret = service.regenerate_credentials()
        assert new_key != old_key
        assert new_secret != old_secret
        service.refresh_from_db()
        assert service.api_key == new_key
        assert service.api_secret == new_secret

    def test_str_representation(self, service: ServiceProduct) -> None:
        """String representation shows the name."""
        assert str(service) == "Test Service"

    def test_default_values(self, service: ServiceProduct) -> None:
        """Default field values are set correctly."""
        assert service.is_active is True
        assert service.allowed_currencies == []
        assert service.allowed_ips == []
        assert service.metadata == {}

    def test_unique_api_key(self, service: ServiceProduct, db) -> None:
        """API keys must be unique across services."""
        from django.db import IntegrityError

        svc2 = ServiceProduct(name="Another", slug="another")
        svc2.api_key = service.api_key  # duplicate key
        with pytest.raises(IntegrityError):
            svc2.save()


# ───────────────────── Model Tests: Payment ──────────────────────────────────


@pytest.mark.django_db
class TestPaymentModel:
    """Tests for the Payment model."""

    def test_amount_in_kobo(self, payment: Payment) -> None:
        """Amount correctly converts to smallest currency unit."""
        assert payment.amount_in_kobo == 100_000

    def test_net_amount(self, payment: Payment) -> None:
        """Net amount = amount - fees."""
        assert payment.net_amount == Decimal("975.00")

    def test_refundable_amount(self, payment: Payment) -> None:
        """Refundable amount = amount - already refunded."""
        assert payment.refundable_amount == Decimal("1000.00")
        payment.refunded_amount = Decimal("300.00")
        assert payment.refundable_amount == Decimal("700.00")

    def test_is_refundable_success(self, payment: Payment) -> None:
        """Successful payments with no full refund are refundable."""
        assert payment.is_refundable is True

    def test_is_refundable_pending(self, pending_payment: Payment) -> None:
        """Pending payments are not refundable."""
        assert pending_payment.is_refundable is False

    def test_is_refundable_fully_refunded(self, payment: Payment) -> None:
        """Fully refunded payments are not refundable."""
        payment.refund_status = Payment.RefundStatus.FULL
        payment.refunded_amount = payment.amount
        assert payment.is_refundable is False

    def test_is_refundable_partial(self, payment: Payment) -> None:
        """Partially refunded payments are still refundable."""
        payment.refund_status = Payment.RefundStatus.PARTIAL
        payment.refunded_amount = Decimal("200.00")
        assert payment.is_refundable is True

    def test_is_successful(self, payment: Payment, pending_payment: Payment) -> None:
        """is_successful checks status correctly."""
        assert payment.is_successful is True
        assert pending_payment.is_successful is False

    def test_str_with_service(self, payment: Payment) -> None:
        """String representation includes service name."""
        s = str(payment)
        assert "Test Service" in s
        assert payment.reference in s
        assert "KES" in s

    def test_str_without_service(self, direct_payment: Payment) -> None:
        """String representation shows 'Direct' for service-less payments."""
        assert "Direct" in str(direct_payment)

    def test_status_choices(self) -> None:
        """All expected status choices exist."""
        statuses = dict(Payment.Status.choices)
        assert "pending" in statuses
        assert "success" in statuses
        assert "failed" in statuses
        assert "abandoned" in statuses

    def test_refund_status_choices(self) -> None:
        """All expected refund status choices exist."""
        choices = dict(Payment.RefundStatus.choices)
        assert "none" in choices
        assert "pending" in choices
        assert "partial" in choices
        assert "full" in choices
        assert "failed" in choices

    def test_currency_choices(self) -> None:
        """All expected currency choices exist."""
        currencies = dict(Payment.Currency.choices)
        assert "KES" in currencies
        assert "USD" in currencies
        assert "NGN" in currencies


# ──────────────────── Model Tests: WebhookDeliveryLog ────────────────────────


@pytest.mark.django_db
class TestWebhookDeliveryLogModel:
    """Tests for the WebhookDeliveryLog model."""

    def test_create_log_entry(self, service: ServiceProduct, payment: Payment) -> None:
        """Can create a webhook delivery log."""
        log = WebhookDeliveryLog.objects.create(
            service=service,
            payment=payment,
            url="https://example.com/webhook/",
            event="payment.success",
            request_headers={"Content-Type": "application/json"},
            request_body={"reference": payment.reference},
            response_status=200,
            response_body="ok",
            attempt=1,
            success=True,
            duration_ms=150,
        )
        assert log.success is True
        assert log.attempt == 1
        assert log.duration_ms == 150

    def test_str_success(self, service: ServiceProduct, payment: Payment) -> None:
        """String representation for successful delivery."""
        log = WebhookDeliveryLog.objects.create(
            service=service,
            payment=payment,
            url="https://example.com/webhook/",
            event="payment.success",
            success=True,
        )
        s = str(log)
        assert "ok" in s
        assert "payment.success" in s

    def test_str_failed(self, service: ServiceProduct, payment: Payment) -> None:
        """String representation for failed delivery."""
        log = WebhookDeliveryLog.objects.create(
            service=service,
            payment=payment,
            url="https://example.com/webhook/",
            event="payment.refunded",
            success=False,
        )
        s = str(log)
        assert "failed" in s


# ──────────────────── Service Layer: Helpers ─────────────────────────────────


class TestServiceHelpers:
    """Tests for payment service helper functions."""

    def test_generate_reference_format(self) -> None:
        """References start with 'acoruss-' and are unique."""
        ref = generate_reference()
        assert ref.startswith("acoruss-")
        assert len(ref) == 20  # acoruss- + 12 hex chars

    def test_generate_reference_uniqueness(self) -> None:
        """Generated references are unique."""
        refs = {generate_reference() for _ in range(100)}
        assert len(refs) == 100

    def test_generate_api_key_format(self) -> None:
        """API keys start with ak_ prefix."""
        key = generate_api_key()
        assert key.startswith("ak_")
        assert len(key) == 51

    def test_generate_api_secret_format(self) -> None:
        """API secrets start with sk_ prefix."""
        secret = generate_api_secret()
        assert secret.startswith("sk_")
        assert len(secret) == 67

    def test_validate_webhook_signature_valid(self, settings) -> None:
        """Valid webhook signature passes validation."""
        settings.PAYSTACK_SECRET_KEY = "test_secret_key"
        payload = b'{"event": "charge.success"}'
        expected_sig = hmac.new(b"test_secret_key", payload, hashlib.sha512).hexdigest()
        assert validate_webhook_signature(payload, expected_sig) is True

    def test_validate_webhook_signature_invalid(self, settings) -> None:
        """Invalid webhook signature fails validation."""
        settings.PAYSTACK_SECRET_KEY = "test_secret_key"
        payload = b'{"event": "charge.success"}'
        assert validate_webhook_signature(payload, "bad_sig") is False

    def test_validate_webhook_signature_no_key(self, settings) -> None:
        """Returns False when Paystack key is not configured."""
        settings.PAYSTACK_SECRET_KEY = ""
        assert validate_webhook_signature(b"data", "sig") is False


# ──────────────────── Webhook Dispatcher ─────────────────────────────────────


class TestWebhookDispatcher:
    """Tests for outbound webhook signing."""

    def test_sign_payload(self) -> None:
        """HMAC SHA256 payload signing works correctly."""
        payload = b'{"event": "payment.success"}'
        secret = "test_secret_123"
        signature = sign_payload(payload, secret)
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert signature == expected

    def test_sign_payload_different_secret(self) -> None:
        """Different secrets produce different signatures."""
        payload = b'{"event": "test"}'
        sig1 = sign_payload(payload, "secret_a")
        sig2 = sign_payload(payload, "secret_b")
        assert sig1 != sig2


# ──────────────── API Auth ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestAPIAuth:
    """Tests for API authentication."""

    def test_missing_auth_header(self, client: Client) -> None:
        """Request without Authorization header returns 401."""
        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "a@b.com", "amount": 100}),
            content_type="application/json",
        )
        assert response.status_code == 401
        data = response.json()
        assert "Authorization" in data["error"]

    def test_invalid_api_key(self, client: Client) -> None:
        """Invalid API key returns 401."""
        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "a@b.com", "amount": 100}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer ak_invalid_key_12345678",
        )
        assert response.status_code == 401

    def test_inactive_service_key(
        self,
        client: Client,
        inactive_service: ServiceProduct,
    ) -> None:
        """Inactive service API key returns 401."""
        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "a@b.com", "amount": 100}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {inactive_service.api_key}",
        )
        assert response.status_code == 401

    def test_ip_not_allowed(self, client: Client, service: ServiceProduct) -> None:
        """Request from non-allowed IP returns 403."""
        service.allowed_ips = ["10.0.0.1"]
        service.save(update_fields=["allowed_ips"])

        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "a@b.com", "amount": 100}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 403


# ──────────────── API Views ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestAPIInitiatePayment:
    """Tests for the payment initiation API endpoint."""

    def test_missing_email(self, client: Client, service: ServiceProduct) -> None:
        """Missing email returns validation error."""
        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"amount": 100}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 400
        data = response.json()
        assert "email" in data.get("details", {})

    def test_invalid_amount(self, client: Client, service: ServiceProduct) -> None:
        """Non-positive amount returns validation error."""
        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "a@b.com", "amount": -50}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 400
        data = response.json()
        assert "amount" in data.get("details", {})

    def test_invalid_currency(self, client: Client, service: ServiceProduct) -> None:
        """Unsupported currency returns validation error."""
        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "a@b.com", "amount": 100, "currency": "XYZ"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 400

    def test_currency_not_allowed_for_service(
        self,
        client: Client,
        service: ServiceProduct,
    ) -> None:
        """Currency not in service's allowed list returns error."""
        service.allowed_currencies = ["KES"]
        service.save(update_fields=["allowed_currencies"])

        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "a@b.com", "amount": 100, "currency": "USD"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 400
        assert "currency" in response.json().get("details", {})

    def test_invalid_json_body(self, client: Client, service: ServiceProduct) -> None:
        """Invalid JSON returns 400."""
        response = client.post(
            "/api/v1/payments/initiate/",
            data="not json",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 400

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_successful_initiation(
        self,
        mock_init: AsyncMock,
        client: Client,
        service: ServiceProduct,
    ) -> None:
        """Successful initiation returns authorization URL."""
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/abc"},
        }
        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps(
                {
                    "email": "customer@example.com",
                    "amount": 500,
                    "currency": "KES",
                    "description": "Test payment",
                    "service_reference": "order-123",
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] is True
        assert "reference" in data["data"]
        assert data["data"]["authorization_url"] == "https://paystack.com/pay/abc"

        # Verify payment was created in the database
        payment = Payment.objects.get(reference=data["data"]["reference"])
        assert payment.service == service
        assert payment.email == "customer@example.com"
        assert payment.amount == Decimal("500.00")
        assert payment.service_reference == "order-123"

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_idempotency_key(
        self,
        mock_init: AsyncMock,
        client: Client,
        service: ServiceProduct,
    ) -> None:
        """Duplicate idempotency key returns existing payment."""
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/first"},
        }
        # First request
        payload = json.dumps(
            {
                "email": "a@b.com",
                "amount": 100,
                "idempotency_key": "unique-key-123",
            }
        )
        resp1 = client.post(
            "/api/v1/payments/initiate/",
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert resp1.status_code == 200
        ref1 = resp1.json()["data"]["reference"]

        # Second request with same idempotency key (should NOT call Paystack again)
        resp2 = client.post(
            "/api/v1/payments/initiate/",
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["reference"] == ref1
        assert mock_init.call_count == 1  # Only called once

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_paystack_failure(
        self,
        mock_init: AsyncMock,
        client: Client,
        service: ServiceProduct,
    ) -> None:
        """Paystack failure returns 502."""
        mock_init.return_value = {"status": False, "message": "Paystack error"}
        response = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "a@b.com", "amount": 100}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 502


@pytest.mark.django_db
class TestAPIPaymentStatus:
    """Tests for the payment status API endpoint."""

    def test_get_existing_payment(
        self,
        client: Client,
        payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Returns payment details for a valid reference."""
        response = client.get(
            f"/api/v1/payments/{payment.reference}/",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["reference"] == payment.reference
        assert data["amount"] == "1000.00"
        assert data["status"] == "success"
        assert data["fees"] == "25.00"

    def test_payment_scoped_to_service(
        self,
        client: Client,
        direct_payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Cannot see payments belonging to other services."""
        response = client.get(
            f"/api/v1/payments/{direct_payment.reference}/",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 404

    def test_nonexistent_reference(self, client: Client, service: ServiceProduct) -> None:
        """Unknown reference returns 404."""
        response = client.get(
            "/api/v1/payments/nonexistent-ref/",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestAPIPaymentList:
    """Tests for the payment list API endpoint."""

    def test_list_service_payments(
        self,
        client: Client,
        payment: Payment,
        pending_payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Lists only payments belonging to the service."""
        response = client.get(
            "/api/v1/payments/",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] == 2
        assert len(data["data"]) == 2

    def test_filter_by_status(
        self,
        client: Client,
        payment: Payment,
        pending_payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Can filter payments by status."""
        response = client.get(
            "/api/v1/payments/?status=success",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        data = response.json()
        assert data["meta"]["total"] == 1
        assert data["data"][0]["status"] == "success"

    def test_excludes_other_services(
        self,
        client: Client,
        payment: Payment,
        direct_payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Only shows payments for the authenticated service."""
        response = client.get(
            "/api/v1/payments/",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        data = response.json()
        refs = [p["reference"] for p in data["data"]]
        assert direct_payment.reference not in refs


@pytest.mark.django_db
class TestAPIRefund:
    """Tests for the refund API endpoint."""

    def test_refund_nonrefundable_payment(
        self,
        client: Client,
        pending_payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Cannot refund a pending payment."""
        response = client.post(
            f"/api/v1/payments/{pending_payment.reference}/refund/",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 400
        assert "not refundable" in response.json()["error"]

    def test_refund_invalid_amount(
        self,
        client: Client,
        payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Refund amount exceeding payment amount is rejected."""
        response = client.post(
            f"/api/v1/payments/{payment.reference}/refund/",
            data=json.dumps({"amount": 99999}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 400

    def test_refund_not_found(self, client: Client, service: ServiceProduct) -> None:
        """Refund for nonexistent payment returns 404."""
        response = client.post(
            "/api/v1/payments/nonexistent-ref/refund/",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
        )
        assert response.status_code == 404

    @patch("apps.payments.api_views.services.create_refund", new_callable=AsyncMock)
    def test_successful_full_refund(
        self,
        mock_refund: AsyncMock,
        client: Client,
        payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Full refund updates payment status."""
        mock_refund.return_value = {
            "status": True,
            "data": {"id": "refund_123", "amount": 100_000},
        }
        with patch("apps.payments.webhook_dispatcher.dispatch_webhook", new_callable=AsyncMock):
            response = client.post(
                f"/api/v1/payments/{payment.reference}/refund/",
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] is True
        assert data["data"]["refund_status"] == "full"

        payment.refresh_from_db()
        assert payment.refund_status == Payment.RefundStatus.FULL
        assert payment.refunded_amount == Decimal("1000.00")

    @patch("apps.payments.api_views.services.create_refund", new_callable=AsyncMock)
    def test_successful_partial_refund(
        self,
        mock_refund: AsyncMock,
        client: Client,
        payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Partial refund updates status to partial."""
        mock_refund.return_value = {
            "status": True,
            "data": {"id": "refund_456", "amount": 30_000},
        }
        with patch("apps.payments.webhook_dispatcher.dispatch_webhook", new_callable=AsyncMock):
            response = client.post(
                f"/api/v1/payments/{payment.reference}/refund/",
                data=json.dumps({"amount": 300, "reason": "Partial return"}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {service.api_key}",
            )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["refund_status"] == "partial"

        payment.refresh_from_db()
        assert payment.refund_status == Payment.RefundStatus.PARTIAL
        assert payment.refunded_amount == Decimal("300.00")


# ──────────── Dashboard Views: Services ──────────────────────────────────────


@pytest.mark.django_db
class TestDashboardServiceViews:
    """Tests for the dashboard service management views."""

    def test_service_list_requires_login(self, client: Client) -> None:
        """Service list redirects unauthenticated users."""
        response = client.get(reverse("core:dashboard_services"))
        assert response.status_code == 302

    def test_service_list_loads(
        self,
        admin_client: Client,
        service: ServiceProduct,
    ) -> None:
        """Service list page loads with services in context."""
        response = admin_client.get(reverse("core:dashboard_services"))
        assert response.status_code == 200
        assert "services" in response.context

    def test_service_create_page_loads(self, admin_client: Client) -> None:
        """Service create page loads."""
        response = admin_client.get(reverse("core:dashboard_service_create"))
        assert response.status_code == 200

    def test_service_create_post(self, admin_client: Client) -> None:
        """Creating a service via POST succeeds."""
        response = admin_client.post(
            reverse("core:dashboard_service_create"),
            data={
                "name": "New Service",
                "slug": "new-service",
                "description": "A new one",
                "webhook_url": "https://example.com/hook/",
                "default_callback_url": "",
                "contact_email": "new@example.com",
                "logo_url": "",
                "allowed_currencies": "[]",
                "allowed_ips": "[]",
            },
        )
        assert response.status_code == 302
        assert ServiceProduct.objects.filter(slug="new-service").exists()

    def test_service_detail_loads(
        self,
        admin_client: Client,
        service: ServiceProduct,
    ) -> None:
        """Service detail page loads with revenue context."""
        response = admin_client.get(reverse("core:dashboard_service_detail", kwargs={"slug": service.slug}))
        assert response.status_code == 200
        assert "total_revenue" in response.context
        assert "net_revenue" in response.context

    def test_service_toggle_active(
        self,
        admin_client: Client,
        service: ServiceProduct,
    ) -> None:
        """Toggle active status works."""
        assert service.is_active is True
        response = admin_client.post(reverse("core:dashboard_service_toggle", kwargs={"slug": service.slug}))
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.is_active is False

    def test_service_regenerate_keys(
        self,
        admin_client: Client,
        service: ServiceProduct,
    ) -> None:
        """Regenerating keys changes credentials."""
        old_key = service.api_key
        response = admin_client.post(reverse("core:dashboard_service_regenerate_keys", kwargs={"slug": service.slug}))
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.api_key != old_key

    def test_service_update_settings(
        self,
        admin_client: Client,
        service: ServiceProduct,
    ) -> None:
        """Updating service settings persists changes."""
        response = admin_client.post(
            reverse("core:dashboard_service_update", kwargs={"slug": service.slug}),
            data={
                "webhook_url": "https://new-webhook.com/hook/",
                "default_callback_url": "https://new-callback.com/done/",
                "contact_email": "new@test.com",
                "allowed_currencies": "KES, USD",
                "allowed_ips": "10.0.0.1, 192.168.1.1",
            },
        )
        assert response.status_code == 302
        service.refresh_from_db()
        assert service.webhook_url == "https://new-webhook.com/hook/"
        assert service.allowed_currencies == ["KES", "USD"]
        assert service.allowed_ips == ["10.0.0.1", "192.168.1.1"]


# ──────────── Dashboard Views: Payments ──────────────────────────────────────


@pytest.mark.django_db
class TestDashboardPaymentViews:
    """Tests for the dashboard payment views."""

    def test_payment_list_loads(
        self,
        admin_client: Client,
        payment: Payment,
    ) -> None:
        """Payment list loads with payments."""
        response = admin_client.get(reverse("core:dashboard_payments"))
        assert response.status_code == 200

    def test_payment_list_filter_by_service(
        self,
        admin_client: Client,
        payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """Can filter payments by service slug."""
        response = admin_client.get(reverse("core:dashboard_payments") + f"?service={service.slug}")
        assert response.status_code == 200

    def test_payment_detail_loads(
        self,
        admin_client: Client,
        payment: Payment,
    ) -> None:
        """Payment detail page loads."""
        response = admin_client.get(reverse("core:dashboard_payment_detail", kwargs={"pk": payment.pk}))
        assert response.status_code == 200
        assert "webhook_logs" in response.context

    def test_payment_export_csv(
        self,
        admin_client: Client,
        payment: Payment,
    ) -> None:
        """CSV export returns correct content type and data."""
        response = admin_client.get(reverse("core:dashboard_payments_export"))
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        content = response.content.decode()
        assert "Reference" in content
        assert payment.reference in content

    def test_payment_export_filter_by_service(
        self,
        admin_client: Client,
        payment: Payment,
        direct_payment: Payment,
        service: ServiceProduct,
    ) -> None:
        """CSV export can be filtered by service."""
        response = admin_client.get(reverse("core:dashboard_payments_export") + f"?service={service.slug}")
        content = response.content.decode()
        assert payment.reference in content
        assert direct_payment.reference not in content


# ──────────────── Public Payment Views ───────────────────────────────────────


@pytest.mark.django_db
class TestPublicPaymentViews:
    """Tests for the public payment pages."""

    def test_payment_page_loads(self, client: Client) -> None:
        """Public payment page loads."""
        response = client.get(reverse("payments:pay"))
        assert response.status_code == 200

    @patch("apps.payments.views.services.initialise_transaction", new_callable=AsyncMock)
    def test_initiate_payment_success(
        self,
        mock_init: AsyncMock,
        client: Client,
    ) -> None:
        """Successful payment initiation redirects to Paystack."""
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/xyz"},
        }
        response = client.post(
            reverse("payments:initiate"),
            data={
                "email": "test@example.com",
                "name": "Test User",
                "amount": "500",
                "currency": "KES",
                "description": "Discovery Call",
            },
        )
        assert response.status_code == 302
        assert "paystack.com" in response.url

    def test_initiate_payment_invalid_amount(self, client: Client) -> None:
        """Invalid amount shows error and redirects back."""
        response = client.post(
            reverse("payments:initiate"),
            data={"email": "test@example.com", "amount": "0", "currency": "KES"},
        )
        assert response.status_code == 302
        assert response.url == reverse("payments:pay")

    def test_initiate_payment_missing_email(self, client: Client) -> None:
        """Missing email shows error and redirects back."""
        response = client.post(
            reverse("payments:initiate"),
            data={"email": "", "amount": "500", "currency": "KES"},
        )
        assert response.status_code == 302

    @patch("apps.payments.views.services.verify_transaction", new_callable=AsyncMock)
    def test_verify_payment_success(
        self,
        mock_verify: AsyncMock,
        client: Client,
        pending_payment: Payment,
    ) -> None:
        """Successful verification updates payment status."""
        mock_verify.return_value = {
            "status": True,
            "data": {
                "status": "success",
                "id": "12345",
                "channel": "card",
                "fees": 1250,
            },
        }
        response = client.get(reverse("payments:verify") + f"?reference={pending_payment.reference}")
        assert response.status_code == 302

        pending_payment.refresh_from_db()
        assert pending_payment.status == Payment.Status.SUCCESS
        assert pending_payment.channel == "card"
        assert pending_payment.fees == Decimal("12.50")

    def test_verify_payment_no_reference(self, client: Client) -> None:
        """Verify with no reference redirects to payment page."""
        response = client.get(reverse("payments:verify"))
        assert response.status_code == 302


# ─────────────── Paystack Webhook View ───────────────────────────────────────


@pytest.mark.django_db
class TestPaystackWebhook:
    """Tests for the Paystack webhook handler."""

    def _make_signature(self, payload: bytes, secret: str) -> str:
        return hmac.new(secret.encode(), payload, hashlib.sha512).hexdigest()

    def test_invalid_signature(self, client: Client, settings) -> None:
        """Invalid signature returns 400."""
        settings.PAYSTACK_SECRET_KEY = "test_key"
        response = client.post(
            reverse("payments:webhook"),
            data=b'{"event": "charge.success"}',
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE="bad_signature",
        )
        assert response.status_code == 400

    def test_charge_success_event(
        self,
        client: Client,
        pending_payment: Payment,
        settings,
    ) -> None:
        """charge.success event updates payment to success."""
        settings.PAYSTACK_SECRET_KEY = "test_key"
        payload = json.dumps(
            {
                "event": "charge.success",
                "data": {
                    "reference": pending_payment.reference,
                    "id": "99999",
                    "channel": "bank",
                    "fees": 750,
                },
            }
        ).encode()
        signature = self._make_signature(payload, "test_key")

        response = client.post(
            reverse("payments:webhook"),
            data=payload,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )
        assert response.status_code == 200

        pending_payment.refresh_from_db()
        assert pending_payment.status == Payment.Status.SUCCESS
        assert pending_payment.channel == "bank"
        assert pending_payment.fees == Decimal("7.50")

    def test_unknown_reference_ignored(
        self,
        client: Client,
        settings,
    ) -> None:
        """Webhook for unknown reference is accepted but ignored."""
        settings.PAYSTACK_SECRET_KEY = "test_key"
        payload = json.dumps(
            {
                "event": "charge.success",
                "data": {"reference": "nonexistent-ref"},
            }
        ).encode()
        signature = self._make_signature(payload, "test_key")

        response = client.post(
            reverse("payments:webhook"),
            data=payload,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )
        assert response.status_code == 200

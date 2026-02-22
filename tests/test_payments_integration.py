"""Integration tests for the payments application.

These tests exercise end-to-end flows across multiple components — models, API
auth, API views, public views, webhooks, and the dashboard — with only external
Paystack HTTP calls mocked out.
"""

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.test import Client
from django.urls import reverse

from apps.payments.models import (
    Payment,
    ServiceProduct,
    WebhookDeliveryLog,
)

# ──────────────────────── Shared Fixtures ────────────────────────────────────


@pytest.fixture
def service_a(db) -> ServiceProduct:
    """First service (KES-only)."""
    return ServiceProduct.objects.create(
        name="Service Alpha",
        slug="service-alpha",
        description="First test service",
        webhook_url="https://alpha.example.com/webhook/",
        default_callback_url="https://alpha.example.com/callback/",
        contact_email="alpha@example.com",
        allowed_currencies=["KES"],
    )


@pytest.fixture
def service_b(db) -> ServiceProduct:
    """Second service (all currencies, no webhook)."""
    return ServiceProduct.objects.create(
        name="Service Beta",
        slug="service-beta",
        description="Second test service",
        contact_email="beta@example.com",
    )


@pytest.fixture
def admin_user(db):
    """Dashboard admin user."""
    from apps.accounts.models import User

    return User.objects.create_user(
        username="integration_admin",
        email="admin@acoruss.com",
        password="integrationpass123",
        is_staff=True,
    )


@pytest.fixture
def admin_client(admin_user) -> Client:
    """Logged-in admin client."""
    c = Client()
    c.login(username="integration_admin", password="integrationpass123")
    return c


def _paystack_signature(payload: bytes, secret: str) -> str:
    """Compute the Paystack webhook HMAC-SHA512 signature."""
    return hmac.new(secret.encode(), payload, hashlib.sha512).hexdigest()


# ═════════════════════════════════════════════════════════════════════════════
#  1. Full API Payment Lifecycle
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPIPaymentLifecycle:
    """Initiate → Paystack webhook confirms → query status → refund."""

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    @patch("apps.payments.api_views.services.create_refund", new_callable=AsyncMock)
    @patch("apps.payments.webhook_dispatcher.dispatch_webhook", new_callable=AsyncMock)
    def test_full_lifecycle(
        self,
        mock_dispatch: AsyncMock,
        mock_refund: AsyncMock,
        mock_init: AsyncMock,
        client: Client,
        service_a: ServiceProduct,
        settings,
    ) -> None:
        """A payment goes through initiation → webhook success → status check → refund."""
        # ── Step 1: Initiate payment via API ─────────────────────────────
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/lifecycle"},
        }
        resp = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps(
                {
                    "email": "lifecycle@example.com",
                    "amount": 2000,
                    "currency": "KES",
                    "description": "Lifecycle test",
                    "service_reference": "order-lifecycle-001",
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 200, resp.json()
        reference = resp.json()["data"]["reference"]
        assert reference.startswith("acoruss-")

        # Verify DB state after initiation
        payment = Payment.objects.get(reference=reference)
        assert payment.status == Payment.Status.PENDING
        assert payment.service == service_a
        assert payment.email == "lifecycle@example.com"
        assert payment.amount == Decimal("2000.00")
        assert payment.service_reference == "order-lifecycle-001"

        # ── Step 2: Paystack webhook confirms payment ────────────────────
        settings.PAYSTACK_SECRET_KEY = "wh_secret_lifecycle"
        webhook_payload = json.dumps(
            {
                "event": "charge.success",
                "data": {
                    "reference": reference,
                    "id": "paystack_tx_99",
                    "channel": "mobile_money",
                    "fees": 3500,
                },
            }
        ).encode()
        signature = _paystack_signature(webhook_payload, "wh_secret_lifecycle")

        resp = client.post(
            reverse("payments:webhook"),
            data=webhook_payload,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )
        assert resp.status_code == 200

        payment.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS
        assert payment.channel == "mobile_money"
        assert payment.fees == Decimal("35.00")
        assert payment.paystack_id == "paystack_tx_99"

        # ── Step 3: Query payment status via API ─────────────────────────
        resp = client.get(
            f"/api/v1/payments/{reference}/",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "success"
        assert data["channel"] == "mobile_money"
        assert data["fees"] == "35.00"
        assert data["amount"] == "2000.00"

        # ── Step 4: Partial refund via API ───────────────────────────────
        mock_refund.return_value = {
            "status": True,
            "data": {"id": "refund_lc_1", "amount": 50_000},
        }
        resp = client.post(
            f"/api/v1/payments/{reference}/refund/",
            data=json.dumps({"amount": 500, "reason": "Partial return"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["refund_status"] == "partial"

        payment.refresh_from_db()
        assert payment.refund_status == Payment.RefundStatus.PARTIAL
        assert payment.refunded_amount == Decimal("500.00")
        assert payment.refundable_amount == Decimal("1500.00")

        # ── Step 5: Full refund of remaining ─────────────────────────────
        mock_refund.return_value = {
            "status": True,
            "data": {"id": "refund_lc_2", "amount": 150_000},
        }
        resp = client.post(
            f"/api/v1/payments/{reference}/refund/",
            data=json.dumps({"amount": 1500}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["refund_status"] == "full"

        payment.refresh_from_db()
        assert payment.refund_status == Payment.RefundStatus.FULL
        assert payment.refunded_amount == Decimal("2000.00")
        assert payment.is_refundable is False

        # ── Step 6: Further refund should be rejected ────────────────────
        resp = client.post(
            f"/api/v1/payments/{reference}/refund/",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 400
        assert "not refundable" in resp.json()["error"]


# ═════════════════════════════════════════════════════════════════════════════
#  2. Multi-Service Isolation
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestMultiServiceIsolation:
    """Payments are strictly scoped to their owning service."""

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_services_cannot_see_each_others_payments(
        self,
        mock_init: AsyncMock,
        client: Client,
        service_a: ServiceProduct,
        service_b: ServiceProduct,
    ) -> None:
        """Service A's payments are invisible to Service B and vice versa."""
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/x"},
        }

        # Service A creates a payment
        resp_a = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "alpha@test.com", "amount": 100, "currency": "KES"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp_a.status_code == 200
        ref_a = resp_a.json()["data"]["reference"]

        # Service B creates a payment
        resp_b = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "beta@test.com", "amount": 200, "currency": "USD"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_b.api_key}",
        )
        assert resp_b.status_code == 200
        ref_b = resp_b.json()["data"]["reference"]

        # Service A can see its own payment
        resp = client.get(
            f"/api/v1/payments/{ref_a}/",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 200

        # Service A CANNOT see Service B's payment
        resp = client.get(
            f"/api/v1/payments/{ref_b}/",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 404

        # Service B CANNOT see Service A's payment
        resp = client.get(
            f"/api/v1/payments/{ref_a}/",
            HTTP_AUTHORIZATION=f"Bearer {service_b.api_key}",
        )
        assert resp.status_code == 404

        # Service A's list contains exactly 1 payment
        resp = client.get(
            "/api/v1/payments/",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.json()["meta"]["total"] == 1
        assert resp.json()["data"][0]["reference"] == ref_a

        # Service B's list contains exactly 1 payment
        resp = client.get(
            "/api/v1/payments/",
            HTTP_AUTHORIZATION=f"Bearer {service_b.api_key}",
        )
        assert resp.json()["meta"]["total"] == 1
        assert resp.json()["data"][0]["reference"] == ref_b

        # Service A cannot refund Service B's payment
        resp = client.post(
            f"/api/v1/payments/{ref_b}/refund/",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
#  3. Currency Restriction Enforcement
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCurrencyRestrictions:
    """Service-level currency allowlists are enforced across the API layer."""

    def test_allowed_currency_accepted_disallowed_rejected(
        self,
        client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """Service A allows only KES — USD is rejected, KES is accepted (validation-level)."""
        # USD → rejected
        resp = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "cur@test.com", "amount": 100, "currency": "USD"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 400
        assert "currency" in resp.json()["details"]

        # KES → accepted (will fail at Paystack mock level, but validation passes)
        with patch(
            "apps.payments.api_views.services.initialise_transaction",
            new_callable=AsyncMock,
            return_value={"status": True, "data": {"authorization_url": "https://paystack.com/pay/ok"}},
        ):
            resp = client.post(
                "/api/v1/payments/initiate/",
                data=json.dumps({"email": "cur@test.com", "amount": 100, "currency": "KES"}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
            )
            assert resp.status_code == 200

    def test_no_restriction_accepts_all(
        self,
        client: Client,
        service_b: ServiceProduct,
    ) -> None:
        """Service B has no currency restriction — all valid currencies pass."""
        for currency in ("KES", "USD", "NGN"):
            with patch(
                "apps.payments.api_views.services.initialise_transaction",
                new_callable=AsyncMock,
                return_value={"status": True, "data": {"authorization_url": "https://paystack.com/pay/any"}},
            ):
                resp = client.post(
                    "/api/v1/payments/initiate/",
                    data=json.dumps({"email": "multi@test.com", "amount": 50, "currency": currency}),
                    content_type="application/json",
                    HTTP_AUTHORIZATION=f"Bearer {service_b.api_key}",
                )
                assert resp.status_code == 200, f"{currency} should be accepted"


# ═════════════════════════════════════════════════════════════════════════════
#  4. Idempotency Across the Stack
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestIdempotency:
    """Idempotency keys guarantee exactly-once payment creation."""

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_duplicate_idempotency_key_returns_same_payment(
        self,
        mock_init: AsyncMock,
        client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """Three identical requests produce only one Payment record."""
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/idem"},
        }
        payload = json.dumps(
            {
                "email": "idem@test.com",
                "amount": 750,
                "currency": "KES",
                "idempotency_key": "idem-key-abc-123",
            }
        )

        references = set()
        for _ in range(3):
            resp = client.post(
                "/api/v1/payments/initiate/",
                data=payload,
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
            )
            assert resp.status_code == 200
            references.add(resp.json()["data"]["reference"])

        # All three requests returned the same reference
        assert len(references) == 1
        # Paystack was called only once
        assert mock_init.call_count == 1
        # Only one record in the DB
        assert Payment.objects.filter(idempotency_key="idem-key-abc-123").count() == 1

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_different_idempotency_keys_create_separate_payments(
        self,
        mock_init: AsyncMock,
        client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """Different idempotency keys create distinct payments."""
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/x"},
        }
        references = set()
        for i in range(3):
            resp = client.post(
                "/api/v1/payments/initiate/",
                data=json.dumps(
                    {
                        "email": "multi@test.com",
                        "amount": 100,
                        "currency": "KES",
                        "idempotency_key": f"key-{i}",
                    }
                ),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
            )
            assert resp.status_code == 200
            references.add(resp.json()["data"]["reference"])

        assert len(references) == 3
        assert mock_init.call_count == 3


# ═════════════════════════════════════════════════════════════════════════════
#  5. Public Payment → Webhook → Service Callback
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestPublicPaymentFlow:
    """End-to-end public payment page → initiate → verify → redirect."""

    @patch("apps.payments.views.services.initialise_transaction", new_callable=AsyncMock)
    @patch("apps.payments.views.services.verify_transaction", new_callable=AsyncMock)
    def test_public_payment_initiate_and_verify(
        self,
        mock_verify: AsyncMock,
        mock_init: AsyncMock,
        client: Client,
    ) -> None:
        """User initiates payment → redirected to Paystack → callback verifies."""
        # Step 1: Page loads
        resp = client.get(reverse("payments:pay"))
        assert resp.status_code == 200

        # Step 2: Initiate
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/pub123"},
        }
        resp = client.post(
            reverse("payments:initiate"),
            data={
                "email": "public@user.com",
                "name": "Public User",
                "amount": "1500",
                "currency": "KES",
                "description": "Discovery Call",
            },
        )
        assert resp.status_code == 302
        assert "paystack.com" in resp.url

        # Fetch the created payment
        payment = Payment.objects.get(email="public@user.com")
        assert payment.status == Payment.Status.PENDING
        assert payment.amount == Decimal("1500.00")
        assert payment.service is None  # Direct/public payment

        # Step 3: Paystack callback → verify
        mock_verify.return_value = {
            "status": True,
            "data": {
                "status": "success",
                "id": "ps_pub_99",
                "channel": "card",
                "fees": 2250,
            },
        }
        resp = client.get(reverse("payments:verify") + f"?reference={payment.reference}")
        assert resp.status_code == 302  # redirects to pay page (no callback_url)

        payment.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS
        assert payment.channel == "card"
        assert payment.fees == Decimal("22.50")
        assert payment.paystack_id == "ps_pub_99"

    @patch("apps.payments.views.services.initialise_transaction", new_callable=AsyncMock)
    @patch("apps.payments.views.services.verify_transaction", new_callable=AsyncMock)
    @patch("apps.payments.webhook_dispatcher.dispatch_webhook", new_callable=AsyncMock)
    def test_service_payment_verify_dispatches_webhook(
        self,
        mock_dispatch: AsyncMock,
        mock_verify: AsyncMock,
        mock_init: AsyncMock,
        client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """Verify for a service-linked payment triggers outbound webhook."""
        # Create a pending payment linked to a service (as if initiated via API)
        payment = Payment.objects.create(
            service=service_a,
            email="webhook@test.com",
            amount=Decimal("800.00"),
            currency="KES",
            reference="acoruss-wh-flow-01",
            status=Payment.Status.PENDING,
            callback_url="https://alpha.example.com/done/",
        )

        mock_verify.return_value = {
            "status": True,
            "data": {
                "status": "success",
                "id": "ps_wh_100",
                "channel": "bank",
                "fees": 1200,
            },
        }
        mock_dispatch.return_value = True

        resp = client.get(reverse("payments:verify") + f"?reference={payment.reference}")
        # Should redirect to the service's callback URL
        assert resp.status_code == 302
        assert "alpha.example.com/done/" in resp.url
        assert f"reference={payment.reference}" in resp.url

        payment.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS

        # Webhook was dispatched
        mock_dispatch.assert_called_once()
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["event"] == "payment.success"
        assert call_kwargs["service"] == service_a

    @patch("apps.payments.views.services.verify_transaction", new_callable=AsyncMock)
    def test_failed_verification_marks_payment_failed(
        self,
        mock_verify: AsyncMock,
        client: Client,
    ) -> None:
        """A failed Paystack verification marks the payment as failed."""
        payment = Payment.objects.create(
            email="fail@test.com",
            amount=Decimal("500.00"),
            currency="KES",
            reference="acoruss-fail-verify",
            status=Payment.Status.PENDING,
        )

        mock_verify.return_value = {
            "status": True,
            "data": {"status": "failed"},
        }
        resp = client.get(reverse("payments:verify") + f"?reference={payment.reference}")
        assert resp.status_code == 302

        payment.refresh_from_db()
        assert payment.status == Payment.Status.FAILED


# ═════════════════════════════════════════════════════════════════════════════
#  6. Paystack Webhook → Outbound Webhook Dispatch
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestWebhookChain:
    """Paystack webhook triggers outbound webhook to the service."""

    @patch("apps.payments.webhook_dispatcher.dispatch_webhook", new_callable=AsyncMock)
    def test_charge_success_triggers_outbound_webhook(
        self,
        mock_dispatch: AsyncMock,
        client: Client,
        service_a: ServiceProduct,
        settings,
    ) -> None:
        """Paystack charge.success → payment updated → webhook dispatched to service."""
        settings.PAYSTACK_SECRET_KEY = "chain_key"

        payment = Payment.objects.create(
            service=service_a,
            email="chain@test.com",
            amount=Decimal("3000.00"),
            currency="KES",
            reference="acoruss-chain-001",
            status=Payment.Status.PENDING,
        )

        payload = json.dumps(
            {
                "event": "charge.success",
                "data": {
                    "reference": payment.reference,
                    "id": "ps_chain_1",
                    "channel": "card",
                    "fees": 4500,
                },
            }
        ).encode()
        sig = _paystack_signature(payload, "chain_key")

        mock_dispatch.return_value = True
        resp = client.post(
            reverse("payments:webhook"),
            data=payload,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=sig,
        )
        assert resp.status_code == 200

        payment.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS
        assert payment.fees == Decimal("45.00")

        # Outbound webhook was dispatched
        mock_dispatch.assert_called_once()
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["event"] == "payment.success"
        assert call_kwargs["service"].pk == service_a.pk

    def test_webhook_for_direct_payment_no_outbound(
        self,
        client: Client,
        settings,
    ) -> None:
        """Paystack webhook for a payment without a service does not attempt outbound."""
        settings.PAYSTACK_SECRET_KEY = "direct_key"

        payment = Payment.objects.create(
            email="direct@test.com",
            amount=Decimal("100.00"),
            currency="USD",
            reference="acoruss-direct-wh",
            status=Payment.Status.PENDING,
        )

        payload = json.dumps(
            {
                "event": "charge.success",
                "data": {
                    "reference": payment.reference,
                    "id": "ps_direct_1",
                    "channel": "ussd",
                    "fees": 150,
                },
            }
        ).encode()
        sig = _paystack_signature(payload, "direct_key")

        with patch(
            "apps.payments.webhook_dispatcher.dispatch_webhook",
            new_callable=AsyncMock,
        ) as mock_dispatch:
            resp = client.post(
                reverse("payments:webhook"),
                data=payload,
                content_type="application/json",
                HTTP_X_PAYSTACK_SIGNATURE=sig,
            )
            assert resp.status_code == 200
            mock_dispatch.assert_not_called()

        payment.refresh_from_db()
        assert payment.status == Payment.Status.SUCCESS

    def test_refund_webhook_event(
        self,
        client: Client,
        service_a: ServiceProduct,
        settings,
    ) -> None:
        """refund.processed event updates payment refund fields."""
        settings.PAYSTACK_SECRET_KEY = "refund_wh_key"

        payment = Payment.objects.create(
            service=service_a,
            email="refwh@test.com",
            amount=Decimal("5000.00"),
            currency="KES",
            reference="acoruss-refwh-001",
            status=Payment.Status.SUCCESS,
        )

        payload = json.dumps(
            {
                "event": "refund.processed",
                "data": {
                    "id": "refund_wh_99",
                    "amount": 200_000,
                    "transaction": {"reference": payment.reference},
                },
            }
        ).encode()
        sig = _paystack_signature(payload, "refund_wh_key")

        with patch(
            "apps.payments.webhook_dispatcher.dispatch_webhook",
            new_callable=AsyncMock,
        ):
            resp = client.post(
                reverse("payments:webhook"),
                data=payload,
                content_type="application/json",
                HTTP_X_PAYSTACK_SIGNATURE=sig,
            )
        assert resp.status_code == 200

        payment.refresh_from_db()
        assert payment.refunded_amount == Decimal("2000.00")
        assert payment.refund_status == Payment.RefundStatus.PARTIAL
        assert payment.paystack_refund_id == "refund_wh_99"


# ═════════════════════════════════════════════════════════════════════════════
#  7. Dashboard Service Onboarding → API Usage
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestServiceOnboardingFlow:
    """Admin creates service in dashboard → API caller uses the credentials."""

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_admin_creates_service_then_api_works(
        self,
        mock_init: AsyncMock,
        admin_client: Client,
        client: Client,
    ) -> None:
        """Complete onboarding flow: dashboard create → API initiate."""
        # ── Dashboard: create a service ─────────────────────────────────
        resp = admin_client.post(
            reverse("core:dashboard_service_create"),
            data={
                "name": "Onboard Test",
                "slug": "onboard-test",
                "description": "Integration onboarding test",
                "webhook_url": "https://onboard.test/hook/",
                "default_callback_url": "https://onboard.test/done/",
                "contact_email": "onboard@test.com",
                "logo_url": "",
                "allowed_currencies": "[]",
                "allowed_ips": "[]",
            },
        )
        assert resp.status_code == 302
        svc = ServiceProduct.objects.get(slug="onboard-test")
        assert svc.api_key.startswith("ak_")
        assert svc.api_secret.startswith("sk_")

        # ── API: use the new service's credentials ──────────────────────
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/onboard"},
        }
        resp = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "new@user.com", "amount": 250, "currency": "KES"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {svc.api_key}",
        )
        assert resp.status_code == 200

        # ── Dashboard: service shows up with payment count ──────────────
        resp = admin_client.get(reverse("core:dashboard_service_detail", kwargs={"slug": "onboard-test"}))
        assert resp.status_code == 200
        assert resp.context["total_payments"] == 1

    def test_admin_toggles_service_disables_api(
        self,
        admin_client: Client,
        client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """Disabling a service via dashboard blocks all API requests."""
        # Ensure service starts active
        assert service_a.is_active is True

        # Toggle off
        resp = admin_client.post(reverse("core:dashboard_service_toggle", kwargs={"slug": service_a.slug}))
        assert resp.status_code == 302
        service_a.refresh_from_db()
        assert service_a.is_active is False

        # API call should now be rejected with 401
        resp = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "blocked@test.com", "amount": 100}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 401

        # Toggle back on
        resp = admin_client.post(reverse("core:dashboard_service_toggle", kwargs={"slug": service_a.slug}))
        service_a.refresh_from_db()
        assert service_a.is_active is True

    def test_admin_regenerates_keys_old_key_rejected(
        self,
        admin_client: Client,
        client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """After regenerating keys, the old API key no longer works."""
        old_key = service_a.api_key

        resp = admin_client.post(reverse("core:dashboard_service_regenerate_keys", kwargs={"slug": service_a.slug}))
        assert resp.status_code == 302
        service_a.refresh_from_db()
        new_key = service_a.api_key
        assert new_key != old_key

        # Old key → 401
        resp = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "regen@test.com", "amount": 100}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {old_key}",
        )
        assert resp.status_code == 401

        # New key → accepted (will fail at Paystack level, but auth passes)
        with patch(
            "apps.payments.api_views.services.initialise_transaction",
            new_callable=AsyncMock,
            return_value={"status": True, "data": {"authorization_url": "https://paystack.com/pay/regen"}},
        ):
            resp = client.post(
                "/api/v1/payments/initiate/",
                data=json.dumps({"email": "regen@test.com", "amount": 100}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {new_key}",
            )
            assert resp.status_code == 200


# ═════════════════════════════════════════════════════════════════════════════
#  8. Dashboard Payment Management
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDashboardPaymentManagement:
    """Dashboard payment list, detail, export, and refund flow."""

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_dashboard_sees_all_service_payments(
        self,
        mock_init: AsyncMock,
        admin_client: Client,
        client: Client,
        service_a: ServiceProduct,
        service_b: ServiceProduct,
    ) -> None:
        """Dashboard shows payments from all services."""
        mock_init.return_value = {
            "status": True,
            "data": {"authorization_url": "https://paystack.com/pay/dash"},
        }

        # Create payments under different services
        for svc in (service_a, service_b):
            client.post(
                "/api/v1/payments/initiate/",
                data=json.dumps({"email": f"{svc.slug}@test.com", "amount": 100}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {svc.api_key}",
            )

        # Also a direct (public) payment
        Payment.objects.create(
            email="public@test.com",
            amount=Decimal("50.00"),
            currency="USD",
            reference="acoruss-dash-pub-1",
        )

        # Dashboard list shows all 3
        resp = admin_client.get(reverse("core:dashboard_payments"))
        assert resp.status_code == 200

        # Filter by service_a
        resp = admin_client.get(reverse("core:dashboard_payments") + f"?service={service_a.slug}")
        assert resp.status_code == 200

        # CSV export includes all payments
        resp = admin_client.get(reverse("core:dashboard_payments_export"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "service-alpha@test.com" in content
        assert "service-beta@test.com" in content
        assert "public@test.com" in content

        # CSV export filtered by service_a
        resp = admin_client.get(reverse("core:dashboard_payments_export") + f"?service={service_a.slug}")
        content = resp.content.decode()
        assert "service-alpha@test.com" in content
        assert "service-beta@test.com" not in content

    @patch("apps.payments.views.services.create_refund", new_callable=AsyncMock)
    @patch("apps.payments.webhook_dispatcher.dispatch_webhook", new_callable=AsyncMock)
    def test_dashboard_refund_flow(
        self,
        mock_dispatch: AsyncMock,
        mock_refund: AsyncMock,
        admin_client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """Admin refunds a payment from the dashboard detail page."""
        payment = Payment.objects.create(
            service=service_a,
            email="dashrefund@test.com",
            amount=Decimal("1000.00"),
            currency="KES",
            reference="acoruss-dashrefund-1",
            status=Payment.Status.SUCCESS,
        )

        # View the payment detail
        resp = admin_client.get(reverse("core:dashboard_payment_detail", kwargs={"pk": payment.pk}))
        assert resp.status_code == 200
        assert resp.context["payment"].reference == payment.reference

        # Initiate partial refund from dashboard
        mock_refund.return_value = {
            "status": True,
            "data": {"id": "ref_dash_1", "amount": 40_000},
        }
        mock_dispatch.return_value = True

        resp = admin_client.post(
            reverse("core:dashboard_payment_refund", kwargs={"pk": payment.pk}),
            data={"refund_amount": "400", "refund_reason": "Customer complaint"},
        )
        assert resp.status_code == 302

        payment.refresh_from_db()
        assert payment.refund_status == Payment.RefundStatus.PARTIAL
        assert payment.refunded_amount == Decimal("400.00")

        # Webhook was dispatched for refund
        mock_dispatch.assert_called_once()
        assert mock_dispatch.call_args.kwargs["event"] == "payment.refunded"


# ═════════════════════════════════════════════════════════════════════════════
#  9. Webhook Delivery & Logging
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestWebhookDeliveryIntegration:
    """Webhook dispatcher creates log entries and handles retries."""

    @pytest.mark.asyncio
    async def test_webhook_delivery_success_creates_log(
        self,
        service_a: ServiceProduct,
    ) -> None:
        """Successful webhook delivery creates a log entry and marks payment."""
        from apps.payments.webhook_dispatcher import dispatch_webhook

        payment = await Payment.objects.acreate(
            service=service_a,
            email="whlog@test.com",
            amount=Decimal("100.00"),
            currency="KES",
            reference="acoruss-whlog-001",
            status=Payment.Status.SUCCESS,
        )

        # Mock the HTTP call to succeed
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"ok"

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = await dispatch_webhook(
                service=service_a,
                payment=payment,
                event="payment.success",
            )

        assert result is True

        # Verify log was created
        logs = await WebhookDeliveryLog.objects.filter(payment=payment).acount()
        assert logs == 1

        log = await WebhookDeliveryLog.objects.filter(payment=payment).afirst()
        assert log.success is True
        assert log.event == "payment.success"
        assert log.response_status == 200
        assert log.attempt == 1

        # Payment was marked as webhook-delivered
        await payment.arefresh_from_db()
        assert payment.webhook_delivered is True
        assert payment.webhook_delivered_at is not None

    @pytest.mark.asyncio
    async def test_webhook_delivery_failure_retries(
        self,
        service_a: ServiceProduct,
    ) -> None:
        """Failed webhook delivery retries and logs each attempt."""
        from apps.payments.webhook_dispatcher import dispatch_webhook

        payment = await Payment.objects.acreate(
            service=service_a,
            email="whretry@test.com",
            amount=Decimal("200.00"),
            currency="KES",
            reference="acoruss-whretry-001",
            status=Payment.Status.SUCCESS,
        )

        # Mock HTTP call to always fail
        with (
            patch(
                "urllib.request.urlopen",
                side_effect=Exception("Connection refused"),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await dispatch_webhook(
                service=service_a,
                payment=payment,
                event="payment.success",
            )

        assert result is False

        # Should have 3 log entries (MAX_RETRIES)
        log_count = await WebhookDeliveryLog.objects.filter(payment=payment).acount()
        assert log_count == 3

        # Each log should have the error recorded
        async for log in WebhookDeliveryLog.objects.filter(payment=payment).order_by("attempt"):
            assert log.success is False
            assert "Connection refused" in log.error_message

        # Payment not marked as delivered
        await payment.arefresh_from_db()
        assert payment.webhook_delivered is False

    @pytest.mark.asyncio
    async def test_no_webhook_url_skips_delivery(
        self,
        service_b: ServiceProduct,
    ) -> None:
        """Service without webhook URL skips delivery entirely."""
        from apps.payments.webhook_dispatcher import dispatch_webhook

        assert service_b.webhook_url == ""

        payment = await Payment.objects.acreate(
            service=service_b,
            email="nowh@test.com",
            amount=Decimal("100.00"),
            currency="KES",
            reference="acoruss-nowh-001",
            status=Payment.Status.SUCCESS,
        )

        result = await dispatch_webhook(
            service=service_b,
            payment=payment,
            event="payment.success",
        )

        assert result is False
        assert await WebhookDeliveryLog.objects.filter(payment=payment).acount() == 0


# ═════════════════════════════════════════════════════════════════════════════
# 10. IP Allowlist Integration
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestIPAllowlistIntegration:
    """IP allowlisting interacts correctly with the full API flow."""

    def test_ip_restriction_updated_via_dashboard_enforced_in_api(
        self,
        admin_client: Client,
        client: Client,
        service_b: ServiceProduct,
    ) -> None:
        """Admin restricts IPs via dashboard → API enforces the restriction."""
        # Initially no IP restriction — API works
        with patch(
            "apps.payments.api_views.services.initialise_transaction",
            new_callable=AsyncMock,
            return_value={"status": True, "data": {"authorization_url": "https://paystack.com/pay/ip"}},
        ):
            resp = client.post(
                "/api/v1/payments/initiate/",
                data=json.dumps({"email": "ip@test.com", "amount": 100}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {service_b.api_key}",
            )
            assert resp.status_code == 200

        # Admin restricts to a specific IP
        resp = admin_client.post(
            reverse("core:dashboard_service_update", kwargs={"slug": service_b.slug}),
            data={
                "webhook_url": "",
                "default_callback_url": "",
                "contact_email": "beta@test.com",
                "allowed_currencies": "",
                "allowed_ips": "10.0.0.1",
            },
        )
        assert resp.status_code == 302
        service_b.refresh_from_db()
        assert service_b.allowed_ips == ["10.0.0.1"]

        # Now API call from test client (127.0.0.1) should be rejected
        resp = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "ip@test.com", "amount": 100}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_b.api_key}",
        )
        assert resp.status_code == 403

        # Remove the restriction
        resp = admin_client.post(
            reverse("core:dashboard_service_update", kwargs={"slug": service_b.slug}),
            data={
                "webhook_url": "",
                "default_callback_url": "",
                "contact_email": "beta@test.com",
                "allowed_currencies": "",
                "allowed_ips": "",
            },
        )
        assert resp.status_code == 302
        service_b.refresh_from_db()
        assert service_b.allowed_ips == []

        # API works again
        with patch(
            "apps.payments.api_views.services.initialise_transaction",
            new_callable=AsyncMock,
            return_value={"status": True, "data": {"authorization_url": "https://paystack.com/pay/ip2"}},
        ):
            resp = client.post(
                "/api/v1/payments/initiate/",
                data=json.dumps({"email": "ip@test.com", "amount": 100}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {service_b.api_key}",
            )
            assert resp.status_code == 200


# ═════════════════════════════════════════════════════════════════════════════
# 11. Paystack Gateway Failure Handling
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestPaystackGatewayFailures:
    """System handles Paystack API failures gracefully."""

    @patch("apps.payments.api_views.services.initialise_transaction", new_callable=AsyncMock)
    def test_initiation_failure_does_not_leave_orphan_auth_url(
        self,
        mock_init: AsyncMock,
        client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """Failed Paystack init creates payment record but no auth URL."""
        mock_init.return_value = {"status": False, "message": "Gateway timeout"}

        resp = client.post(
            "/api/v1/payments/initiate/",
            data=json.dumps({"email": "fail@test.com", "amount": 100, "currency": "KES"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 502

        # Payment record was still created (pending)
        payment = Payment.objects.get(email="fail@test.com")
        assert payment.status == Payment.Status.PENDING
        assert payment.authorization_url == ""

    @patch("apps.payments.api_views.services.create_refund", new_callable=AsyncMock)
    def test_refund_gateway_failure_returns_502(
        self,
        mock_refund: AsyncMock,
        client: Client,
        service_a: ServiceProduct,
    ) -> None:
        """Paystack refund failure returns 502 without modifying payment."""
        payment = Payment.objects.create(
            service=service_a,
            email="refundfail@test.com",
            amount=Decimal("500.00"),
            currency="KES",
            reference="acoruss-rf-fail-01",
            status=Payment.Status.SUCCESS,
        )

        mock_refund.return_value = {"status": False, "message": "Insufficient balance"}

        resp = client.post(
            f"/api/v1/payments/{payment.reference}/refund/",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_a.api_key}",
        )
        assert resp.status_code == 502

        # Payment was NOT modified
        payment.refresh_from_db()
        assert payment.refund_status == Payment.RefundStatus.NONE
        assert payment.refunded_amount == Decimal("0.00")

    @patch("apps.payments.views.services.initialise_transaction", new_callable=AsyncMock)
    def test_public_initiation_failure_redirects_with_error(
        self,
        mock_init: AsyncMock,
        client: Client,
    ) -> None:
        """Public payment form shows error when Paystack is down."""
        mock_init.return_value = {"status": False, "message": "Service unavailable"}

        resp = client.post(
            reverse("payments:initiate"),
            data={
                "email": "down@test.com",
                "name": "Down User",
                "amount": "500",
                "currency": "KES",
            },
        )
        assert resp.status_code == 302
        assert resp.url == reverse("payments:pay")

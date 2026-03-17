"""Tests for the core app views."""

import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestPublicViews:
    """Test public-facing views."""

    def test_index_page_loads(self, client: Client) -> None:
        """Test that the homepage loads successfully."""
        response = client.get(reverse("core:index"))
        assert response.status_code == 200

    def test_privacy_policy_loads(self, client: Client) -> None:
        """Test that the privacy policy page loads."""
        response = client.get(reverse("core:privacy_policy"))
        assert response.status_code == 200

    def test_terms_of_service_loads(self, client: Client) -> None:
        """Test that the terms of service page loads."""
        response = client.get(reverse("core:terms_of_service"))
        assert response.status_code == 200

    def test_dashboard_requires_login(self, client: Client) -> None:
        """Test that the dashboard redirects to login."""
        response = client.get(reverse("core:dashboard"))
        assert response.status_code == 302
        assert "/dashboard/login/" in response.url

    def test_dashboard_login_page_loads(self, client: Client) -> None:
        """Test that the dashboard login page loads."""
        response = client.get(reverse("core:dashboard_login"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestExchangeRateEndpoint:
    """Test the /api/rates/usd-kes/ exchange rate endpoint."""

    URL = reverse("core:exchange_rate")

    @patch(
        "apps.payments.currency_service.get_exchange_rate",
        new_callable=AsyncMock,
        return_value=Decimal("129.50"),
    )
    @pytest.mark.asyncio
    async def test_returns_rate(self, mock_rate, async_client) -> None:
        """Test that a valid rate is returned."""
        response = await async_client.get(self.URL)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["rate"] == 129.50
        assert data["from"] == "USD"
        assert data["to"] == "KES"
        mock_rate.assert_awaited_once_with("USD", "KES")

    @patch(
        "apps.payments.currency_service.get_exchange_rate",
        new_callable=AsyncMock,
        side_effect=RuntimeError("API down"),
    )
    @pytest.mark.asyncio
    async def test_returns_503_on_failure(self, mock_rate, async_client) -> None:
        """Test that a 503 is returned when the rate API fails."""
        response = await async_client.get(self.URL)
        assert response.status_code == 503
        data = json.loads(response.content)
        assert "error" in data

    def test_only_get_allowed(self, client: Client) -> None:
        """Test that POST, PUT, DELETE, PATCH are rejected."""
        for method in ["post", "put", "delete", "patch"]:
            response = getattr(client, method)(self.URL)
            assert response.status_code == 405, f"{method.upper()} should be 405"

    @patch(
        "apps.payments.currency_service.get_exchange_rate",
        new_callable=AsyncMock,
        return_value=Decimal("129.50"),
    )
    @pytest.mark.asyncio
    async def test_response_is_json(self, mock_rate, async_client) -> None:
        """Test that content type is JSON."""
        response = await async_client.get(self.URL)
        assert response["Content-Type"] == "application/json"

    @patch(
        "apps.payments.currency_service.get_exchange_rate",
        new_callable=AsyncMock,
        return_value=Decimal("129.50"),
    )
    @pytest.mark.asyncio
    async def test_no_sensitive_data_leaked(self, mock_rate, async_client) -> None:
        """Test that the response contains only the expected fields."""
        response = await async_client.get(self.URL)
        data = json.loads(response.content)
        allowed_keys = {"rate", "from", "to"}
        assert set(data.keys()) == allowed_keys

    @patch(
        "apps.payments.currency_service.get_exchange_rate",
        new_callable=AsyncMock,
        return_value=Decimal("129.50"),
    )
    @pytest.mark.asyncio
    async def test_no_auth_required(self, mock_rate, async_client) -> None:
        """Test that the endpoint is publicly accessible (no login needed)."""
        response = await async_client.get(self.URL)
        assert response.status_code == 200

    @patch(
        "apps.payments.currency_service.get_exchange_rate",
        new_callable=AsyncMock,
        return_value=Decimal("129.50"),
    )
    @pytest.mark.asyncio
    async def test_no_cookies_set(self, mock_rate, async_client) -> None:
        """Test that no cookies/auth tokens are set on the response."""
        response = await async_client.get(self.URL)
        assert not response.cookies, "Endpoint should not set any cookies"

    def test_does_not_accept_query_params_injection(self, client: Client) -> None:
        """Test that arbitrary query params don't cause errors."""
        response = client.get(self.URL + "?currency=EUR&callback=alert(1)")
        # Should either return 200 (ignored params) or the normal response
        assert response.status_code in (200, 503)

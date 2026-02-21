"""Tests for the core app views."""

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

"""Core app views."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Public homepage."""

    template_name = "index.html"


class PrivacyPolicyView(TemplateView):
    """Privacy policy page."""

    template_name = "privacy_policy.html"


class TermsOfServiceView(TemplateView):
    """Terms of service page."""

    template_name = "terms_of_service.html"


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that requires the user to be an admin."""

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_admin or user.is_superuser or user.is_acoruss_member


class DashboardView(AdminRequiredMixin, TemplateView):
    """Admin dashboard home page."""

    template_name = "dashboard/home.html"

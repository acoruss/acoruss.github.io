"""Core app views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from .models import ContactSubmission


class IndexView(TemplateView):
    """Public homepage."""

    template_name = "index.html"


class ServicesView(TemplateView):
    """Services page with tabbed categories."""

    template_name = "services.html"


class PricingView(TemplateView):
    """Pricing page with buckets and support plans."""

    template_name = "pricing.html"


class ProjectsView(TemplateView):
    """Projects showcase page."""

    template_name = "projects.html"


class AboutView(TemplateView):
    """About us page."""

    template_name = "about.html"


class ContactView(TemplateView):
    """Contact us page."""

    template_name = "contact.html"


class ContactSubmitView(View):
    """Handle contact form submissions."""

    async def post(self, request: HttpRequest) -> HttpResponse:
        """Process the contact form POST request."""
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        company = request.POST.get("company", "").strip()
        phone = request.POST.get("phone", "").strip()
        project_type = request.POST.get("project_type", "").strip()
        message = request.POST.get("message", "").strip()

        if not name or not email or not message:
            messages.error(request, "Please fill in all required fields.")
            return redirect("core:contact")

        await ContactSubmission.objects.acreate(
            name=name,
            email=email,
            company=company,
            phone=phone,
            project_type=project_type,
            message=message,
        )

        messages.success(
            request,
            "Thank you for reaching out! We'll get back to you within 24 hours.",
        )
        return redirect("core:contact")


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

"""Core app views."""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .models import ContactSubmission
from .services import send_contact_notification

logger = logging.getLogger(__name__)


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

        submission = await ContactSubmission.objects.acreate(
            name=name,
            email=email,
            company=company,
            phone=phone,
            project_type=project_type,
            message=message,
        )

        # Send email notification to team
        await send_contact_notification(submission)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_submissions"] = ContactSubmission.objects.count()
        context["unread_submissions"] = ContactSubmission.objects.filter(is_read=False).count()
        context["recent_submissions"] = ContactSubmission.objects.all()[:5]
        return context


class ContactSubmissionsListView(AdminRequiredMixin, ListView):
    """List all contact form submissions."""

    model = ContactSubmission
    template_name = "dashboard/contacts/list.html"
    context_object_name = "submissions"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get("status")
        if status == "unread":
            qs = qs.filter(is_read=False)
        elif status == "read":
            qs = qs.filter(is_read=True)
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                models.Q(name__icontains=search)
                | models.Q(email__icontains=search)
                | models.Q(company__icontains=search)
                | models.Q(message__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_count"] = ContactSubmission.objects.count()
        context["unread_count"] = ContactSubmission.objects.filter(is_read=False).count()
        context["current_status"] = self.request.GET.get("status", "all")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ContactSubmissionDetailView(AdminRequiredMixin, DetailView):
    """View a single contact submission."""

    model = ContactSubmission
    template_name = "dashboard/contacts/detail.html"
    context_object_name = "submission"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=["is_read", "updated_at"])
        return obj


class ContactSubmissionMarkReadView(AdminRequiredMixin, View):
    """Toggle read/unread status of a contact submission."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        try:
            submission = ContactSubmission.objects.get(pk=pk)
        except ContactSubmission.DoesNotExist:
            messages.error(request, "Submission not found.")
            return redirect("core:dashboard_contacts")

        submission.is_read = not submission.is_read
        submission.save(update_fields=["is_read", "updated_at"])
        status = "read" if submission.is_read else "unread"
        messages.success(request, f"Marked as {status}.")
        return redirect("core:dashboard_contact_detail", pk=pk)

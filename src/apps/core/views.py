"""Core app views."""

import logging
import xml.etree.ElementTree as ET
from html import unescape
from re import sub as re_sub

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .models import ContactSubmission
from .services import send_contact_notification

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency if payments isn't migrated yet
_Payment = None


def _get_payment_model():
    global _Payment
    if _Payment is None:
        from apps.payments.models import Payment

        _Payment = Payment
    return _Payment


class RobotsTxtView(View):
    """Serve robots.txt to discourage crawlers from probing non-existent paths."""

    ROBOTS_TXT = (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /services/\n"
        "Allow: /pricing/\n"
        "Allow: /projects/\n"
        "Allow: /our-products/\n"
        "Allow: /about-us/\n"
        "Allow: /contact-us/\n"
        "Allow: /privacy-policy/\n"
        "Allow: /terms-of-service/\n"
        "\n"
        "Disallow: /admin/\n"
        "Disallow: /dashboard/\n"
        "Disallow: /api/\n"
        "Disallow: /payments/\n"
        "\n"
        "Sitemap: https://acoruss.com/sitemap.xml\n"
    )

    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(self.ROBOTS_TXT, content_type="text/plain")


class SecurityTxtView(View):
    """Serve .well-known/security.txt per RFC 9116."""

    SECURITY_TXT = (
        "Contact: mailto:security@acoruss.com\n"
        "Preferred-Languages: en\n"
        "Canonical: https://acoruss.com/.well-known/security.txt\n"
    )

    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(self.SECURITY_TXT, content_type="text/plain")


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


class ProductsView(TemplateView):
    """Our products page — products built and powered by Acoruss."""

    template_name = "products.html"


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
        Payment = _get_payment_model()  # noqa: N806
        context["total_submissions"] = ContactSubmission.objects.count()
        context["unread_submissions"] = ContactSubmission.objects.filter(is_read=False).count()
        context["recent_submissions"] = ContactSubmission.objects.all()[:5]
        context["total_payments"] = Payment.objects.count()
        context["successful_payments"] = Payment.objects.filter(status=Payment.Status.SUCCESS).count()

        from apps.payments.models import ServiceProduct

        context["total_services"] = ServiceProduct.objects.count()
        context["active_services"] = ServiceProduct.objects.filter(is_active=True).count()
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


class PaymentListView(AdminRequiredMixin, ListView):
    """Dashboard view listing Paystack payment transactions."""

    template_name = "dashboard/payments/list.html"
    context_object_name = "payments"
    paginate_by = 20

    def get_queryset(self):
        Payment = _get_payment_model()  # noqa: N806
        qs = Payment.objects.select_related("service").all()
        status = self.request.GET.get("status")
        if status and status in dict(Payment.Status.choices):
            qs = qs.filter(status=status)
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                models.Q(reference__icontains=search)
                | models.Q(email__icontains=search)
                | models.Q(name__icontains=search)
                | models.Q(service_reference__icontains=search)
            )
        service_slug = self.request.GET.get("service")
        if service_slug:
            qs = qs.filter(service__slug=service_slug)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Payment = _get_payment_model()  # noqa: N806
        context["total_count"] = Payment.objects.count()
        context["success_count"] = Payment.objects.filter(status=Payment.Status.SUCCESS).count()
        context["pending_count"] = Payment.objects.filter(status=Payment.Status.PENDING).count()
        context["current_status"] = self.request.GET.get("status", "all")
        context["search_query"] = self.request.GET.get("q", "")
        context["status_choices"] = Payment.Status.choices
        context["current_service"] = self.request.GET.get("service", "")

        from apps.payments.models import ServiceProduct

        context["services"] = ServiceProduct.objects.filter(is_active=True).order_by("name")
        return context


class AnalyticsView(AdminRequiredMixin, TemplateView):
    """Dashboard analytics overview page."""

    template_name = "dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        from datetime import timedelta

        from django.utils import timezone

        context = super().get_context_data(**kwargs)
        Payment = _get_payment_model()  # noqa: N806

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # Contact metrics
        context["total_contacts"] = ContactSubmission.objects.count()
        context["contacts_30d"] = ContactSubmission.objects.filter(created_at__gte=thirty_days_ago).count()
        context["unread_contacts"] = ContactSubmission.objects.filter(is_read=False).count()

        # Payment metrics
        context["total_payments"] = Payment.objects.count()
        context["successful_payments"] = Payment.objects.filter(status=Payment.Status.SUCCESS).count()
        context["payments_30d"] = Payment.objects.filter(created_at__gte=thirty_days_ago).count()

        # Revenue
        from django.db.models import Sum

        revenue = Payment.objects.filter(status=Payment.Status.SUCCESS).aggregate(total=Sum("amount")).get("total") or 0
        context["total_revenue"] = revenue

        revenue_30d = (
            Payment.objects.filter(
                status=Payment.Status.SUCCESS,
                created_at__gte=thirty_days_ago,
            )
            .aggregate(total=Sum("amount"))
            .get("total")
            or 0
        )
        context["revenue_30d"] = revenue_30d

        # Service product stats
        from apps.payments.models import ServiceProduct

        context["total_services"] = ServiceProduct.objects.count()
        context["active_services"] = ServiceProduct.objects.filter(is_active=True).count()

        # Recent activity
        context["recent_contacts"] = ContactSubmission.objects.all()[:5]
        context["recent_payments"] = Payment.objects.select_related("service").all()[:5]

        return context


class BlogFeedView(View):
    """Proxy Substack RSS feed and return JSON for the blog section."""

    FEED_URL = "https://acoruss.substack.com/feed"
    CACHE_TIMEOUT = 60 * 15  # 15 minutes

    async def get(self, request: HttpRequest) -> JsonResponse:
        import asyncio
        from urllib.request import Request, urlopen

        try:
            loop = asyncio.get_event_loop()
            req = Request(self.FEED_URL, headers={"User-Agent": "Acoruss/1.0"})  # noqa: S310
            body = await loop.run_in_executor(None, lambda: urlopen(req, timeout=10).read())  # noqa: S310
            root = ET.fromstring(body)  # noqa: S314

            posts = []
            for item in root.findall(".//item")[:6]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                description = item.findtext("description", "")
                # Strip HTML tags and decode entities for summary
                summary = unescape(re_sub(r"<[^>]+>", "", description))[:200]

                posts.append(
                    {
                        "title": title,
                        "link": link,
                        "published": pub_date,
                        "summary": summary,
                    }
                )

            return JsonResponse(posts, safe=False)
        except Exception:
            logger.exception("Failed to fetch blog feed")
            return JsonResponse([], safe=False)

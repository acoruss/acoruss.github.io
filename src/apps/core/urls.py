"""Core app URL configuration."""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from apps.payments import views as payment_views

from . import views

app_name = "core"

urlpatterns = [
    # Public pages
    path("", views.IndexView.as_view(), name="index"),
    path("services/", views.ServicesView.as_view(), name="services"),
    path("pricing/", views.PricingView.as_view(), name="pricing"),
    path("projects/", views.ProjectsView.as_view(), name="projects"),
    path("about-us/", views.AboutView.as_view(), name="about"),
    path("contact-us/", views.ContactView.as_view(), name="contact"),
    path("contact-us/submit/", views.ContactSubmitView.as_view(), name="contact_submit"),
    path("privacy-policy/", views.PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("terms-of-service/", views.TermsOfServiceView.as_view(), name="terms_of_service"),
    # API
    path("api/blog-feed/", views.BlogFeedView.as_view(), name="blog_feed"),
    # Dashboard
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("dashboard/contacts/", views.ContactSubmissionsListView.as_view(), name="dashboard_contacts"),
    path("dashboard/contacts/<int:pk>/", views.ContactSubmissionDetailView.as_view(), name="dashboard_contact_detail"),
    path(
        "dashboard/contacts/<int:pk>/toggle-read/",
        views.ContactSubmissionMarkReadView.as_view(),
        name="dashboard_contact_toggle_read",
    ),
    path("dashboard/payments/", views.PaymentListView.as_view(), name="dashboard_payments"),
    path("dashboard/payments/export/", payment_views.PaymentExportView.as_view(), name="dashboard_payments_export"),
    path("dashboard/payments/<int:pk>/", payment_views.PaymentDetailView.as_view(), name="dashboard_payment_detail"),
    path(
        "dashboard/payments/<int:pk>/refund/",
        payment_views.PaymentRefundView.as_view(),
        name="dashboard_payment_refund",
    ),
    path("dashboard/services/", payment_views.ServiceListView.as_view(), name="dashboard_services"),
    path("dashboard/services/create/", payment_views.ServiceCreateView.as_view(), name="dashboard_service_create"),
    path("dashboard/services/<slug:slug>/", payment_views.ServiceDetailView.as_view(), name="dashboard_service_detail"),
    path(
        "dashboard/services/<slug:slug>/toggle/",
        payment_views.ServiceToggleActiveView.as_view(),
        name="dashboard_service_toggle",
    ),
    path(
        "dashboard/services/<slug:slug>/regenerate-keys/",
        payment_views.ServiceRegenerateKeysView.as_view(),
        name="dashboard_service_regenerate_keys",
    ),
    path(
        "dashboard/services/<slug:slug>/update/",
        payment_views.ServiceUpdateView.as_view(),
        name="dashboard_service_update",
    ),
    path("dashboard/analytics/", views.AnalyticsView.as_view(), name="dashboard_analytics"),
    path(
        "dashboard/login/",
        LoginView.as_view(template_name="dashboard/login.html"),
        name="dashboard_login",
    ),
    path("dashboard/logout/", LogoutView.as_view(), name="dashboard_logout"),
]

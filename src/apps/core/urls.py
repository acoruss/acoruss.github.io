"""Core app URL configuration."""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

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
    # Dashboard
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path(
        "dashboard/login/",
        LoginView.as_view(template_name="dashboard/login.html"),
        name="dashboard_login",
    ),
    path("dashboard/logout/", LogoutView.as_view(), name="dashboard_logout"),
]

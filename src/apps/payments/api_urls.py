"""API URL configuration for service-to-service payment endpoints."""

from django.urls import path

from . import api_views

app_name = "payments_api"

urlpatterns = [
    path("payments/initiate/", api_views.APIInitiatePaymentView.as_view(), name="initiate"),
    path("payments/<str:reference>/", api_views.APIPaymentStatusView.as_view(), name="status"),
    path("payments/<str:reference>/refund/", api_views.APIRefundView.as_view(), name="refund"),
    path("payments/", api_views.APIPaymentListView.as_view(), name="list"),
]

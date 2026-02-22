"""Payment URL configuration."""

from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.PaymentPageView.as_view(), name="pay"),
    path("initiate/", views.InitiatePaymentView.as_view(), name="initiate"),
    path("verify/", views.VerifyPaymentView.as_view(), name="verify"),
    path("webhook/", views.PaystackWebhookView.as_view(), name="webhook"),
]

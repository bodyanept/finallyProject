from django.urls import path
from .views import PaymentCreateAPIView, PaymentConfirmAPIView, PaymentWebhookAPIView

urlpatterns = [
    path('payments/mock/create/', PaymentCreateAPIView.as_view(), name='api-payments-mock-create'),
    path('payments/mock/confirm/', PaymentConfirmAPIView.as_view(), name='api-payments-mock-confirm'),
    path('payments/mock/webhook/', PaymentWebhookAPIView.as_view(), name='api-payments-mock-webhook'),
]

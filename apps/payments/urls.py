from django.urls import path
from .views import PaymentYooKassaWebhookAPIView

urlpatterns = [
    path('payments/yookassa/webhook/', PaymentYooKassaWebhookAPIView.as_view(), name='api-payments-yookassa-webhook'),
]

from django.urls import path
from .views import OrderListAPIView, OrderDetailAPIView, CheckoutAPIView

urlpatterns = [
    path('orders/', OrderListAPIView.as_view(), name='api-orders'),
    path('orders/<int:pk>/', OrderDetailAPIView.as_view(), name='api-orders-detail'),
    path('checkout/', CheckoutAPIView.as_view(), name='api-checkout'),
]

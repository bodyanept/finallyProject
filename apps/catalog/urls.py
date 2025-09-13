from django.urls import path
from .views import ProductListAPIView, ProductDetailAPIView

urlpatterns = [
    path('products/', ProductListAPIView.as_view(), name='api-products-list'),
    path('products/<slug:slug>/', ProductDetailAPIView.as_view(), name='api-products-detail'),
]

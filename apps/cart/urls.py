from django.urls import path
from .views import CartRetrieveView, CartItemAddView, CartItemUpdateView

urlpatterns = [
    path('cart/', CartRetrieveView.as_view(), name='api-cart'),
    path('cart/items/', CartItemAddView.as_view(), name='api-cart-item-add'),
    path('cart/items/<int:item_id>/', CartItemUpdateView.as_view(), name='api-cart-item-update'),
]

from django.urls import path
from .views import home
from apps.catalog.views import site_catalog, site_product_detail
from apps.cart.views import site_cart, site_cart_set_quantity, site_cart_remove_item, site_mini_cart
from apps.orders.views import site_checkout
from apps.accounts.views import account_home, garage_add, garage_delete

urlpatterns = [
    path('', home, name='home'),
    path('catalog/', site_catalog, name='site-catalog'),
    path('parts/<slug:slug>/', site_product_detail, name='site-product-detail'),
    path('cart/', site_cart, name='site-cart'),
    path('cart/set/<int:item_id>/', site_cart_set_quantity, name='site-cart-set'),
    path('cart/remove/<int:item_id>/', site_cart_remove_item, name='site-cart-remove'),
    path('mini-cart/', site_mini_cart, name='site-mini-cart'),
    path('checkout/', site_checkout, name='site-checkout'),
    # Account
    path('account/', account_home, name='account-home'),
    path('account/garage/add/', garage_add, name='account-garage-add'),
    path('account/garage/<int:pk>/delete/', garage_delete, name='account-garage-delete'),
]

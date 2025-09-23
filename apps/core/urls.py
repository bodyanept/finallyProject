from django.urls import path
from .views import home
from apps.catalog.views import site_catalog, site_product_detail
from apps.cart.views import site_cart, site_cart_set_quantity, site_cart_remove_item, site_cart_remove_selected, site_mini_cart
from apps.orders.views import site_checkout, site_orders_list, site_order_detail
from apps.accounts.views import (
    account_home,
    garage_add,
    garage_delete,
    register_start,
    register_step1,
    register_step2,
    register_step3,
    register_step4,
    logout_user,
    login_choice,
    login_signin,
)

urlpatterns = [
    path('', home, name='home'),
    path('catalog/', site_catalog, name='site-catalog'),
    path('parts/<slug:slug>/', site_product_detail, name='site-product-detail'),
    path('cart/', site_cart, name='site-cart'),
    path('cart/set/<int:item_id>/', site_cart_set_quantity, name='site-cart-set'),
    path('cart/remove/<int:item_id>/', site_cart_remove_item, name='site-cart-remove'),
    path('cart/remove-selected/', site_cart_remove_selected, name='site-cart-remove-selected'),
    path('mini-cart/', site_mini_cart, name='site-mini-cart'),
    path('checkout/', site_checkout, name='site-checkout'),
    path('account/orders/', site_orders_list, name='site-orders-list'),
    path('account/orders/<int:pk>/', site_order_detail, name='site-order-detail'),
    # Account
    path('account/', account_home, name='account-home'),
    path('account/garage/add/', garage_add, name='account-garage-add'),
    path('account/garage/<int:pk>/delete/', garage_delete, name='account-garage-delete'),
    path('logout/', logout_user, name='logout'),
    path('login/', login_choice, name='login-choice'),
    path('login/signin/', login_signin, name='login-signin'),
    # Registration (multi-step)
    path('register/', register_start, name='register-start'),
    path('register/step1/', register_step1, name='register-step1'),
    path('register/step2/', register_step2, name='register-step2'),
    path('register/step3/', register_step3, name='register-step3'),
    path('register/step4/', register_step4, name='register-step4'),
]


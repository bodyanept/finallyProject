from __future__ import annotations

from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Product
from .models import Order, OrderItem
from .serializers import OrderSerializer
from apps.payments_mock.models import PaymentMock
from apps.accounts.models import Address


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Order.objects.all()

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


class CheckoutAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_method = request.data.get('payment_method', 'card')
        # use user's cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = list(cart.items.select_related('product'))
        if not items:
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=request.user, payment_method=payment_method, status='created')
        for it in items:
            OrderItem.objects.create(
                order=order,
                product=it.product,
                quantity=it.quantity,
                unit_price=it.price_at_add,
            )
        order.recalc_total()
        order.save()

        # Do not delete cart items to allow re-try scenarios, but commonly we clear
        cart.items.all().delete()

        data = OrderSerializer(order).data
        return Response(data, status=status.HTTP_201_CREATED)


# ---------------------- Site (HTML) checkout ----------------------
from django.shortcuts import render, redirect  # noqa: E402
from django.conf import settings  # noqa: E402
from django.views.decorators.http import require_http_methods  # noqa: E402


@require_http_methods(["GET", "POST"])
def site_checkout(request):
    """Simple server-rendered checkout to demonstrate the flow.
    Requires authentication to create an order.
    """
    context = {}

    if not request.user.is_authenticated:
        context.update({
            'need_login': True,
            'message': 'Для оформления заказа войдите (можно через /admin).',
        })
        return render(request, 'orders/checkout.html', context)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related('product'))
    if request.method == 'GET':
        addr = Address.objects.filter(user=request.user).first()
        context.update({'items': items, 'cart': cart, 'address': addr})
        return render(request, 'orders/checkout.html', context)

    # POST: create order and process payment
    payment_method = request.POST.get('payment_method', 'card')

    if not items:
        return redirect('/cart/')

    order = Order.objects.create(user=request.user, payment_method=payment_method, status='created')
    for it in items:
        OrderItem.objects.create(order=order, product=it.product, quantity=it.quantity, unit_price=it.price_at_add)
    order.recalc_total()
    order.save()
    # Balance/wallet payments are processed immediately without external mock
    if payment_method in ('balance', 'wallet'):
        # Attempt to debit user's balance
        from apps.accounts.models import BalanceTransaction
        if request.user.balance >= order.total:
            request.user.balance = request.user.balance - order.total
            request.user.save()
            BalanceTransaction.objects.create(user=request.user, order=order, amount=order.total, type='debit')
            order.status = 'paid'
            order.save()
            # Clear cart only on success
            cart.items.all().delete()
            context.update({'order': order, 'result': 'succeeded'})
            return render(request, 'orders/checkout.html', context)
        else:
            order.status = 'failed'
            order.save()
            # Show topup modal suggestion
            deficit = (order.total - request.user.balance)
            context.update({'order': order, 'result': 'failed', 'need_topup': True, 'topup_deficit': deficit})
            return render(request, 'orders/checkout.html', context)
    # Real provider redirect (YooKassa) when enabled
    if getattr(settings, 'USE_REAL_PAYMENTS', False) and getattr(settings, 'PAYMENTS_PROVIDER', 'mock') == 'yookassa' and payment_method in ('card', 'sbp'):
        try:
            from apps.payments.provider import create_yookassa_payment
            return_url = f"{getattr(settings, 'SITE_BASE_URL', 'http://localhost:8000')}/account/"
            confirmation_url = create_yookassa_payment(order, payment_method, return_url)
            # Do not clear cart; finalize via webhook
            return redirect(confirmation_url)
        except Exception:
            # Fallback to demo behavior if provider call fails
            pass

    # Card payments: collect card fields and approve immediately (demo)
    if payment_method == 'card':
        # In demo, we approve immediately without external gateway
        order.status = 'paid'
        order.save()
        # Clear cart only on success
        cart.items.all().delete()
        context.update({'order': order, 'result': 'succeeded'})
        return render(request, 'orders/checkout.html', context)

    # Fallback for other methods (if any): mark as processing
    order.status = 'processing'
    order.save()

    context.update({'order': order, 'result': 'processing'})
    return render(request, 'orders/checkout.html', context)


# ---------------------- Site (HTML) orders list/detail ----------------------
from django.contrib.auth.decorators import login_required  # noqa: E402


@login_required
def site_orders_list(request):
    """List current user's orders with statuses."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/orders_list.html', {'orders': orders})


@login_required
def site_order_detail(request, pk: int):
    """Show a single order if it belongs to current user."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    items = order.items.select_related('product').all()
    return render(request, 'orders/order_detail.html', {'order': order, 'items': items})

from __future__ import annotations

from decimal import Decimal
from typing import Tuple

from rest_framework import status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.catalog.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


def ensure_cart(request) -> Tuple[Cart, bool]:
    """Return current cart for user or session. Creates if not exists.
    Stores cart id in session for guests.
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart, created

    # Guest via session
    if not request.session.session_key:
        request.session.save()
    cart_id = request.session.get("cart_id")
    cart = None
    if cart_id:
        cart = Cart.objects.filter(id=cart_id, user__isnull=True).first()
    if not cart:
        cart = Cart.objects.create(user=None)
        request.session["cart_id"] = cart.id
        request.session.modified = True
        return cart, True
    return cart, False


class CartRetrieveView(views.APIView):
    def get(self, request):
        cart, _ = ensure_cart(request)
        data = CartSerializer(cart).data
        return Response(data)


class CartItemAddView(views.APIView):
    def post(self, request):
        cart, _ = ensure_cart(request)
        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))
        if quantity < 1:
            quantity = 1
        product = get_object_or_404(Product, id=product_id)

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": 0, "price_at_add": product.price}
        )
        item.quantity = item.quantity + quantity
        # keep original price_at_add on subsequent adds
        if created:
            item.price_at_add = product.price
        item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemUpdateView(views.APIView):
    def patch(self, request, item_id: int):
        cart, _ = ensure_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        quantity = int(request.data.get("quantity", item.quantity))
        if quantity < 1:
            quantity = 1
        item.quantity = quantity
        item.save()
        return Response(CartSerializer(cart).data)

    def delete(self, request, item_id: int):
        cart, _ = ensure_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        return Response(CartSerializer(cart).data)


# ---------------------- Site (HTML) view ----------------------
from django.shortcuts import render  # at end to avoid circular in some tools


def site_cart(request):
    cart, _ = ensure_cart(request)
    items = cart.items.select_related('product').all()
    context = {
        'cart': cart,
        'items': items,
    }
    return render(request, 'cart/cart.html', context)


from django.views.decorators.http import require_POST
from django.shortcuts import redirect


@require_POST
def site_cart_set_quantity(request, item_id: int):
    cart, _ = ensure_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    try:
        quantity = int(request.POST.get('quantity', item.quantity))
    except (TypeError, ValueError):
        quantity = item.quantity
    if quantity < 1:
        quantity = 1
    item.quantity = quantity
    item.save()
    return redirect('/cart/')


@require_POST
def site_cart_remove_item(request, item_id: int):
    cart, _ = ensure_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect('/cart/')


def site_mini_cart(request):
    cart, _ = ensure_cart(request)
    items = cart.items.select_related('product').all()
    context = {
        'cart': cart,
        'items': items,
    }
    return render(request, 'cart/mini_cart.html', context)

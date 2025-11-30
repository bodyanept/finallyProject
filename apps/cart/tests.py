from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.catalog.models import Category, Product
from .models import Cart, CartItem


class CartTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Электрика", slug="elektrika")
        self.product = Product.objects.create(
            name="Аккумулятор Bosch 104",
            slug="bosch-104-akb-1004",
            sku="AKB-1004",
            description="test",
            manufacturer="Bosch",
            price=Decimal("4213.00"),
            in_stock=10,
            images=["https://example.com/img.jpg"],
            category=self.cat,
        )
        self.product2 = Product.objects.create(
            name="Генератор Valeo",
            slug="valeo-gen-2001",
            sku="GEN-2001",
            description="Генератор",
            manufacturer="Valeo",
            price=Decimal("1500.00"),
            in_stock=5,
            images=["https://example.com/img3.jpg"],
            category=self.cat,
        )
        self.api = APIClient()

    def test_api_cart_add_update_delete(self):
        # Add item
        resp = self.api.post('/api/cart/items/', {"product": self.product.id, "quantity": 2}, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(len(data['items']), 1)
        item_id = data['items'][0]['id']
        # Update quantity via PATCH
        resp = self.api.patch(f'/api/cart/items/{item_id}/', {"quantity": 5}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['items'][0]['quantity'], 5)
        # Delete item
        resp = self.api.delete(f'/api/cart/items/{item_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['items']), 0)

    def test_api_cart_retrieve_total_after_add(self):
        # Add two items and GET cart
        self.api.post('/api/cart/items/', {"product": self.product.id, "quantity": 2}, format='json')
        resp = self.api.get('/api/cart/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['items']), 1)
        # total = 2 * 4213.00
        self.assertEqual(str(data['total']), str(Decimal('8426.00')))

    def test_api_cart_add_htmx_returns_204(self):
        resp = self.api.post('/api/cart/items/', {"product": self.product.id, "quantity": 1}, format='json', HTTP_HX_REQUEST='true')
        self.assertEqual(resp.status_code, 204)
        self.assertIn('HX-Trigger', resp)

    def test_site_cart_set_quantity_and_remove(self):
        cart, _ = Cart.objects.get_or_create(user=None)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1, price_at_add=self.product.price)
        # Attach cart to session by visiting a page to create session
        self.client.get('/')
        session = self.client.session
        session['cart_id'] = cart.id
        session.save()
        # Set quantity
        resp = self.client.post(f'/cart/set/{item.id}/', {"quantity": 4})
        self.assertIn(resp.status_code, (302, 301))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)
        # Remove item
        resp = self.client.post(f'/cart/remove/{item.id}/')
        self.assertIn(resp.status_code, (302, 301))
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_site_cart_remove_selected_redirect_and_xhr(self):
        cart, _ = Cart.objects.get_or_create(user=None)
        a = CartItem.objects.create(cart=cart, product=self.product, quantity=1, price_at_add=self.product.price)
        b = CartItem.objects.create(cart=cart, product=self.product2, quantity=2, price_at_add=self.product2.price)
        # attach session
        self.client.get('/')
        s = self.client.session
        s['cart_id'] = cart.id
        s.save()
        # Regular form redirect
        resp = self.client.post('/cart/remove-selected/', {"items": [a.id]}, follow=False)
        self.assertIn(resp.status_code, (302, 301))
        self.assertFalse(CartItem.objects.filter(id=a.id).exists())
        self.assertTrue(CartItem.objects.filter(id=b.id).exists())
        # XHR JSON should return 204
        import json
        resp = self.client.post('/cart/remove-selected/', data=json.dumps({"items": [b.id]}), content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(CartItem.objects.filter(id=b.id).exists())

    def test_site_mini_cart_view(self):
        cart, _ = Cart.objects.get_or_create(user=None)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, price_at_add=self.product.price)
        # attach session
        self.client.get('/')
        s = self.client.session
        s['cart_id'] = cart.id
        s.save()
        resp = self.client.get('/mini-cart/')
        self.assertEqual(resp.status_code, 200)

# Create your tests here.

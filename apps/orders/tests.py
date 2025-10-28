from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.catalog.models import Category, Product
from apps.orders.models import Order, OrderItem
from apps.cart.models import Cart, CartItem
from decimal import Decimal
from apps.orders.serializers import OrderSerializer


class OrdersTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="u1@example.com", password="pass123")
        self.other = User.objects.create_user(email="u2@example.com", password="pass123")

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

    def test_order_model_defaults_and_tracking_number(self):
        order = Order.objects.create(user=self.user, payment_method="card")
        # fulfillment_status default
        self.assertEqual(order.fulfillment_status, "placed")
        # tracking_number should be auto-filled after first save
        self.assertTrue(order.tracking_number.startswith("ZC"))
        self.assertEqual(len(order.tracking_number), 8)  # ZC + 6 digits

    def test_order_recalc_total(self):
        order = Order.objects.create(user=self.user, payment_method="card")
        OrderItem.objects.create(order=order, product=self.product, quantity=2, unit_price=self.product.price)
        OrderItem.objects.create(order=order, product=self.product, quantity=1, unit_price=Decimal("100.50"))
        total = order.recalc_total()
        self.assertEqual(total, Decimal("8526.50"))

    def _prepare_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        cart.items.all().delete()
        CartItem.objects.create(cart=cart, product=self.product, quantity=3, price_at_add=self.product.price)
        return cart

    def test_checkout_creates_order_and_items_card(self):
        self._prepare_cart(self.user)
        client = APIClient()
        client.force_authenticate(self.user)
        url = reverse("api-checkout")
        resp = client.post(url, {"payment_method": "card"}, format="json")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        # Order fields present including new ones
        self.assertIn("fulfillment_status", data)
        self.assertIn("tracking_number", data)
        # Items created and cart cleared
        order = Order.objects.get(id=data["id"])
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 3)
        # API endpoint leaves status as 'created'
        self.assertEqual(order.status, "created")

    def test_orders_list_only_own(self):
        # create two orders
        o1 = Order.objects.create(user=self.user, payment_method="card")
        o2 = Order.objects.create(user=self.other, payment_method="card")
        client = APIClient()
        client.force_authenticate(self.user)
        url = reverse("api-orders")
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        ids = [x["id"] for x in resp.json()["results"]] if isinstance(resp.json(), dict) and "results" in resp.json() else [x["id"] for x in resp.json()]
        self.assertIn(o1.id, ids)
        self.assertNotIn(o2.id, ids)

    def test_order_detail_permission(self):
        order = Order.objects.create(user=self.user, payment_method="card")
        client = APIClient()
        client.force_authenticate(self.other)
        url = reverse("api-orders-detail", kwargs={"pk": order.id})
        resp = client.get(url)
        # permission denied
        self.assertIn(resp.status_code, (403, 404))

    def test_order_serializer_includes_new_fields(self):
        order = Order.objects.create(user=self.user, payment_method="card")
        data = OrderSerializer(order).data
        self.assertIn("fulfillment_status", data)
        self.assertIn("tracking_number", data)
        self.assertEqual(data["fulfillment_status"], "placed")
        self.assertTrue(data["tracking_number"].startswith("ZC"))

    # -------- Site (HTML) views --------
    def test_site_checkout_requires_auth(self):
        from django.urls import reverse as dj_reverse
        url = dj_reverse('site-checkout')
        resp = self.client.get(url)
        # Page hints to login
        self.assertContains(resp, 'Для оформления заказа войдите', status_code=200)

    def test_site_checkout_card_flow_paid_and_cart_cleared(self):
        # login
        self.client.login(email=self.user.email, password='pass123')
        # prepare cart
        self._prepare_cart(self.user)
        # GET checkout page
        resp = self.client.get('/checkout/')
        self.assertEqual(resp.status_code, 200)
        # POST checkout
        resp = self.client.post('/checkout/', {'payment_method': 'card'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'succeeded')
        # last order is paid and cart cleared
        order = Order.objects.filter(user=self.user).latest('created_at')
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 3)
        self.assertEqual(Cart.objects.get(user=self.user).items.count(), 0)

    def test_site_orders_pages_require_auth_and_show_own(self):
        # Create orders
        o1 = Order.objects.create(user=self.user, payment_method='card')
        o2 = Order.objects.create(user=self.other, payment_method='card')
        # anon redirected or forbidden: try list
        resp = self.client.get('/account/orders/')
        self.assertIn(resp.status_code, (302, 301))
        # login and check list contains only own
        self.client.login(email=self.user.email, password='pass123')
        resp = self.client.get('/account/orders/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f"{o1.id}")
        # detail of other's order -> 404
        resp = self.client.get(f'/account/orders/{o2.id}/')
        self.assertEqual(resp.status_code, 404)

# Create your tests here.

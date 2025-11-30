from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.orders.models import Order


class YooKassaWebhookTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='yk@example.com', password='pass1234')
        self.order = Order.objects.create(user=self.user, payment_method='card', status='created')
        self.client = APIClient()

    def test_webhook_payment_succeeded_sets_paid(self):
        payload = {
            'event': 'payment.succeeded',
            'object': {
                'id': '2f2f2f',
                'amount': {'value': '10.00', 'currency': 'RUB'},
                'metadata': {'order_id': self.order.id},
            }
        }
        resp = self.client.post('/api/payments/yookassa/webhook/', payload, format='json')
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_webhook_payment_canceled_sets_failed(self):
        payload = {
            'event': 'payment.canceled',
            'object': {
                'id': '3a3a3a',
                'amount': {'value': '10.00', 'currency': 'RUB'},
                'metadata': {'order_id': self.order.id},
            }
        }
        resp = self.client.post('/api/payments/yookassa/webhook/', payload, format='json')
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')

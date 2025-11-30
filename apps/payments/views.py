from __future__ import annotations

from rest_framework import permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.orders.models import Order


class PaymentYooKassaWebhookAPIView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Expected payload structure (simplified):
        # {
        #   "event": "payment.succeeded" | "payment.canceled" | "payment.waiting_for_capture" | ...,
        #   "object": {
        #       "id": "<payment_id>",
        #       "amount": {"value": "100.00", "currency": "RUB"},
        #       "metadata": {"order_id": 123}
        #   }
        # }
        event = request.data.get('event')
        obj = request.data.get('object') or {}
        metadata = obj.get('metadata') or {}
        order_id = metadata.get('order_id')
        if not order_id:
            return Response({'detail': 'order_id missing'}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=order_id)

        # Map event to order status
        if event == 'payment.succeeded':
            order.status = 'paid'
            order.save()
            return Response({'status': 'paid'})
        if event in ('payment.canceled', 'payment.failed', 'refund.succeeded'):
            order.status = 'failed'
            order.save()
            return Response({'status': 'failed'})

        # For other interim events, acknowledge
        return Response({'status': 'ignored'}, status=status.HTTP_202_ACCEPTED)

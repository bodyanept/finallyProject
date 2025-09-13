from __future__ import annotations

from rest_framework import permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.orders.models import Order
from .models import PaymentMock


class PaymentCreateAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        scenario = request.data.get('scenario', 'success')
        method = request.data.get('method', 'card')

        order = get_object_or_404(Order, id=order_id, user=request.user)
        payment = PaymentMock.objects.create(order=order, scenario=scenario, status='created')
        return Response({
            'payment_id': payment.id,
            'client_secret': payment.client_secret,
            'status': payment.status,
        }, status=status.HTTP_201_CREATED)


class PaymentConfirmAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('payment_id')
        payment = get_object_or_404(PaymentMock, id=payment_id, order__user=request.user)

        if payment.scenario == 'success':
            payment.status = 'succeeded'
            payment.order.status = 'paid'
            payment.order.save()
            payment.save()
            return Response({'status': 'succeeded'})
        elif payment.scenario == 'fail':
            payment.status = 'failed'
            payment.order.status = 'failed'
            payment.order.save()
            payment.save()
            return Response({'status': 'failed'})
        else:
            payment.status = 'processing'
            payment.save()
            return Response({'status': 'processing'}, status=status.HTTP_202_ACCEPTED)


class PaymentWebhookAPIView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payment_id = request.data.get('payment_id')
        result = request.data.get('result', 'succeeded')  # default success
        payment = get_object_or_404(PaymentMock, id=payment_id)

        if payment.status != 'processing':
            return Response({'detail': 'Not in processing state'}, status=status.HTTP_400_BAD_REQUEST)

        if result == 'succeeded':
            payment.status = 'succeeded'
            payment.order.status = 'paid'
        else:
            payment.status = 'failed'
            payment.order.status = 'failed'
        payment.order.save()
        payment.save()
        return Response({'status': payment.status})

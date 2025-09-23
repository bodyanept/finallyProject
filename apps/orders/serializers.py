from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "product_sku", "quantity", "unit_price"]
        read_only_fields = ("unit_price",)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "total",
            "status",
            "payment_method",
            "fulfillment_status",
            "tracking_number",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = ("user", "total", "status", "created_at", "updated_at", "tracking_number")

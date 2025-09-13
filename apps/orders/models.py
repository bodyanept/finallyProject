from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.catalog.models import Product


class Order(models.Model):
    STATUS_CHOICES = (
        ("created", "Created"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
    )
    PAYMENT_METHOD_CHOICES = (
        ("wallet", "Wallet"),
        ("card", "Card"),
        ("balance", "Balance"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="created")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Order #{self.pk} — {self.user.email} — {self.status}"

    def recalc_total(self) -> Decimal:
        total = sum((i.quantity * i.unit_price for i in self.items.all()), start=Decimal("0.00"))
        self.total = total.quantize(Decimal("0.01"))
        return self.total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.product} x {self.quantity}"

# Create your models here.

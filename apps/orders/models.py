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
    FULFILLMENT_CHOICES = (
        ("placed", "Оформлен"),
        ("packed", "Собран"),
        ("shipped", "Отправлен"),
        ("ready", "Доставлен в пункт выдачи"),
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
    fulfillment_status = models.CharField(max_length=12, choices=FULFILLMENT_CHOICES, default="placed")
    tracking_number = models.CharField(max_length=32, blank=True, default="")
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

    def save(self, *args, **kwargs):  # pragma: no cover - trivial
        super().save(*args, **kwargs)
        # Ensure tracking number exists after first save (have id)
        if not self.tracking_number:
            self.tracking_number = f"ZC{self.id:06d}"
            super().save(update_fields=["tracking_number"]) 


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.product} x {self.quantity}"

# Create your models here.

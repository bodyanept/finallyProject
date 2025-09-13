from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="carts", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Cart #{self.pk} for {self.user or 'guest'}"

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), start=Decimal("0.00"))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_add = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.product} x {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return (self.price_at_add * self.quantity).quantize(Decimal("0.01"))

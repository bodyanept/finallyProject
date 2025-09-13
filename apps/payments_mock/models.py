from __future__ import annotations

import uuid
from django.db import models
from django.utils import timezone

from apps.orders.models import Order


class PaymentMock(models.Model):
    SCENARIO_CHOICES = (
        ("success", "Success"),
        ("fail", "Fail"),
        ("pending", "Pending"),
    )
    STATUS_CHOICES = (
        ("created", "Created"),
        ("processing", "Processing"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    scenario = models.CharField(max_length=10, choices=SCENARIO_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="created")
    client_secret = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"PaymentMock #{self.pk} for order {self.order_id}: {self.status} ({self.scenario})"

# Create your models here.

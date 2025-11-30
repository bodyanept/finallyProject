from __future__ import annotations

import uuid
from django.db import models
from django.utils import timezone

from apps.orders.models import Order


class PaymentMock(models.Model):
    SCENARIO_CHOICES = (
        ("success", "Успех"),
        ("fail", "Ошибка"),
        ("pending", "В ожидании"),
    )
    STATUS_CHOICES = (
        ("created", "Создан"),
        ("processing", "Обрабатывается"),
        ("succeeded", "Успешен"),
        ("failed", "Неуспешен"),
    )

    order = models.ForeignKey(Order, verbose_name="Заказ", on_delete=models.CASCADE, related_name="payments")
    scenario = models.CharField("Сценарий", max_length=10, choices=SCENARIO_CHOICES)
    status = models.CharField("Статус", max_length=12, choices=STATUS_CHOICES, default="created")
    client_secret = models.UUIDField("Секрет клиента", default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Тестовый платёж"
        verbose_name_plural = "Тестовые платежи"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"PaymentMock #{self.pk} for order {self.order_id}: {self.status} ({self.scenario})"

# Create your models here.

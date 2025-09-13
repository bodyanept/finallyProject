from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    manufacturer = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    in_stock = models.PositiveIntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    compatibility = models.JSONField(default=list, blank=True, help_text="Список объектов {make, model, year}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} ({self.sku})"


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_history")
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="price_changes"
    )
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.product} {self.old_price} -> {self.new_price}"


class ProductChangeLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="change_logs")
    field = models.CharField(max_length=120)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="product_changes"
    )
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.product} | {self.field}: {self.old_value} -> {self.new_value}"


# Signals to auto-fill slug and record changes
@receiver(pre_save, sender=Product)
def set_slug_on_product(sender, instance: Product, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


@receiver(pre_save, sender=Category)
def set_slug_on_category(sender, instance: Category, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


@receiver(pre_save, sender=Product)
def capture_original_product(sender, instance: Product, **kwargs):
    # Stash original values on the instance to compare in post_save
    if instance.pk:
        try:
            original = Product.objects.get(pk=instance.pk)
            instance._original = {
                "name": original.name,
                "description": original.description,
                "manufacturer": original.manufacturer,
                "price": original.price,
                "in_stock": original.in_stock,
                "images": original.images,
                "compatibility": original.compatibility,
                "category_id": original.category_id,
            }
        except Product.DoesNotExist:  # pragma: no cover - defensive
            instance._original = {}
    else:
        instance._original = {}


@receiver(post_save, sender=Product)
def log_product_changes(sender, instance: Product, created: bool, **kwargs):
    # No logging on create
    original = getattr(instance, "_original", {}) or {}
    if created or not original:
        return

    # Track selected fields
    fields_to_track = [
        "name",
        "description",
        "manufacturer",
        "price",
        "in_stock",
        "images",
        "compatibility",
        "category_id",
    ]

    for field in fields_to_track:
        old = original.get(field)
        new = getattr(instance, field if field != "category_id" else "category_id")
        if old != new:
            ProductChangeLog.objects.create(
                product=instance,
                field=field,
                old_value=str(old),
                new_value=str(new),
            )

    # Special case: price history
    if original.get("price") != instance.price:
        PriceHistory.objects.create(
            product=instance,
            old_price=original.get("price") or instance.price,
            new_price=instance.price,
            reason="manual change",
        )

# Create your models here.

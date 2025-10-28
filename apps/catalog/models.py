from __future__ import annotations

import random
from urllib.parse import quote
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

# Labels per keyword group (for building a guaranteed-correct placeholder image)
KEYWORD_LABELS = [
    (['масляный фильтр', 'фильтр масляный', 'oil filter'], 'Масляный фильтр'),
    (['воздушный фильтр', 'фильтр воздушный', 'air filter'], 'Воздушный фильтр'),
    (['салонный фильтр', 'фильтр салона', 'cabin filter'], 'Салонный фильтр'),
    (['топливный фильтр', 'фильтр топлива', 'fuel filter'], 'Топливный фильтр'),
    (['тормозные колодки', 'колодки', 'колодка', 'brake pads'], 'Тормозные колодки'),
    (['тормозной диск', 'диск тормозной', 'тормозные диски', 'brake disc'], 'Тормозной диск'),
    (['амортизатор', 'стойка амортизатора', 'стойка', 'shock absorber'], 'Амортизатор'),
    (['аккумулятор', 'акб', 'аккум', 'battery'], 'Аккумулятор'),
    (['свеча зажигания', 'свечи', 'свечка', 'spark plug'], 'Свеча зажигания'),
    (['ремень грм', 'ремень', 'грм', 'timing belt'], 'Ремень ГРМ'),
    (['щетки стеклоочистителя', 'щётки', 'щетка', 'щётка', 'дворники', 'wiper'], 'Щётки стеклоочистителя'),
    (['моторное масло', 'масло моторное', 'engine oil', 'масло 5w', '5w-30', '5w30', 'масло'], 'Моторное масло'),
    (['термостат', 'клапан термостата', 'thermostat'], 'Термостат'),
    (['радиатор', 'радиатор охлаждения', 'радиатор двигателя', 'radiator'], 'Радиатор охлаждения'),
]


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


# ---------------------- Image auto-pick by product name ----------------------
# Curated demo images (Unsplash). Feel free to replace with your own static assets.
KEYWORD_IMAGES = [
    # Filters
    ([
        'масляный фильтр', 'фильтр масляный', 'oil filter',
    ], [
        'https://images.unsplash.com/photo-1542362567-b07e54358753?w=800',
        'https://images.unsplash.com/photo-1511919884226-fd3cad34687c?w=800',
    ]),
    ([
        'воздушный фильтр', 'фильтр воздушный', 'air filter'
    ], [
        'https://images.unsplash.com/photo-1617814693417-b874ac4b51ed?w=800',
        'https://images.unsplash.com/photo-1581609833330-7f32662c7ccb?w=800',
    ]),
    ([
        'салонный фильтр', 'фильтр салона', 'cabin filter'
    ], [
        'https://images.unsplash.com/photo-1532635223-7b5d20bbe4b5?w=800',
    ]),
    ([
        'топливный фильтр', 'фильтр топлива', 'fuel filter'
    ], [
        'https://images.unsplash.com/photo-1606229365485-83f69ba4aa64?w=800',
    ]),
    # Brakes
    ([
        'тормозные колодки', 'колодки', 'колодка', 'brake pads'
    ], [
        'https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800',
    ]),
    ([
        'тормозной диск', 'диск тормозной', 'тормозные диски', 'brake disc'
    ], [
        'https://images.unsplash.com/photo-1520975922284-7b14e9a6f208?w=800',
    ]),
    # Suspension
    ([
        'амортизатор', 'стойка амортизатора', 'стойка', 'shock absorber'
    ], [
        'https://images.unsplash.com/photo-1518306727298-4c448be9a99a?w=800',
    ]),
    # Electrical
    ([
        'аккумулятор', 'акб', 'аккум', 'battery'
    ], [
        'https://images.unsplash.com/photo-1599966519407-2ad0ee23d374?w=800',
        'https://images.unsplash.com/photo-1584622781635-a12763b21c2f?w=800',
    ]),
    ([
        'свеча зажигания', 'свечи', 'свечка', 'spark plug'
    ], [
        'https://images.unsplash.com/photo-1628543102646-fc5aa0ee33ea?w=800',
    ]),
    ([
        'стартер', 'стартерный', 'starter'
    ], [
        'https://images.unsplash.com/photo-1517554558809-9b4971b38f39?w=800',
    ]),
    ([
        'генератор', 'альтернатор', 'alternator'
    ], [
        'https://images.unsplash.com/photo-1518544801976-3e188bc06147?w=800',
    ]),
    # Belts/Wipers/Oil
    ([
        'ремень грм', 'ремень', 'грм', 'timing belt'
    ], [
        'https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=800',
    ]),
    ([
        'щетки стеклоочистителя', 'щётки', 'щетка', 'щётка', 'дворники', 'wiper'
    ], [
        'https://images.unsplash.com/photo-1617137968427-85924c800a4c?w=800',
    ]),
    ([
        'моторное масло', 'масло моторное', 'engine oil', 'масло 5w', '5w-30', '5w30', 'масло'
    ], [
        'https://images.unsplash.com/photo-1581091215367-59ab6b514dff?w=800',
    ]),
    # Cooling
    ([
        'термостат', 'клапан термостата', 'thermostat'
    ], [
        'https://images.unsplash.com/photo-1570531492292-4253df3817c5?w=800',
    ]),
    ([
        'радиатор', 'радиатор охлаждения', 'радиатор двигателя', 'radiator'
    ], [
        'https://images.unsplash.com/photo-1592853625600-47d63a9dcc01?w=800',
    ]),
]


def _match_label(name: str) -> str | None:
    text = (name or '').casefold()
    for keywords, label in KEYWORD_LABELS:
        if any(k in text for k in keywords):
            return label
    return None


def pick_images_for_name(name: str) -> list[str]:
    text = (name or '').casefold()
    result: list[str] = []
    label = _match_label(name)
    if label:
        # Build a guaranteed-correct placeholder as the first image
        placeholder = f"https://via.placeholder.com/800x600.png?text={quote(label)}"
        result.append(placeholder)
    for keywords, imgs in KEYWORD_IMAGES:
        if any(k in text for k in keywords):
            # return 1-2 curated images for variety
            if len(imgs) > 1:
                result.extend(random.sample(imgs, k=min(2, len(imgs))))
            else:
                result.extend(imgs)
            break
    return result


@receiver(pre_save, sender=Product)
def ensure_images_by_name(sender, instance: Product, **kwargs):
    """If product has no images, try to guess images by its name."""
    try:
        imgs = instance.images or []
    except Exception:  # JSONField might be None
        imgs = []
    # Normalize: keep only non-empty strings
    imgs = [s.strip() for s in imgs if isinstance(s, str) and s.strip()]
    if not imgs:
        guessed = pick_images_for_name(instance.name)
        if guessed:
            instance.images = guessed
        else:
            instance.images = []
    else:
        # Save back cleaned images so we don't keep blanks
        instance.images = imgs


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

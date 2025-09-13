from __future__ import annotations

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Category, Product


CATEGORIES = [
    ("Тормозная система", "tormoza"),
    ("Фильтры", "filtry"),
    ("Подвеска", "podveska"),
    ("Электрика", "elektrika"),
    ("Масла и жидкости", "masla"),
]

MAKES = {
    "Toyota": ["Corolla", "Camry", "RAV4"],
    "Honda": ["Civic", "Accord", "CR-V"],
    "BMW": ["3 Series", "5 Series"],
    "Hyundai": ["Elantra", "Tucson"],
}

IMAGES = [
    "https://images.unsplash.com/photo-1511919884226-fd3cad34687c?w=800",
    "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800",
    "https://images.unsplash.com/photo-1542362567-b07e54358753?w=800",
]


class Command(BaseCommand):
    help = "Seed demo data: categories and products"

    def handle(self, *args, **options):
        # Categories
        slug_to_cat = {}
        for name, slug in CATEGORIES:
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            slug_to_cat[slug] = cat
        self.stdout.write(self.style.SUCCESS(f"Categories ensured: {len(slug_to_cat)}"))

        # Products
        total = 0
        used_skus = set(Product.objects.values_list("sku", flat=True))
        for i in range(1, 61):
            cat = random.choice(list(slug_to_cat.values()))
            name = f"Деталь {i}"
            slug = slugify(f"detal-{i}")
            sku = f"SKU-{1000 + i}"
            if sku in used_skus:
                continue
            used_skus.add(sku)

            price = Decimal(random.randint(500, 20000)) / Decimal("1.00")
            in_stock = random.randint(0, 50)
            make = random.choice(list(MAKES.keys()))
            model = random.choice(MAKES[make])
            year = random.choice([2010, 2012, 2015, 2018, 2020, 2022])
            compatibility = [{"make": make, "model": model, "year": year}]

            Product.objects.create(
                name=name,
                slug=slug,
                sku=sku,
                description="Учебный товар для демонстрации функций.",
                manufacturer=random.choice(["Bosch", "Valeo", "Delphi", "Denso"]),
                price=price,
                in_stock=in_stock,
                images=random.sample(IMAGES, k=random.randint(1, 3)),
                category=cat,
                compatibility=compatibility,
            )
            total += 1

        self.stdout.write(self.style.SUCCESS(f"Products created: {total}"))

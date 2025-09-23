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
    ("Система охлаждения", "cooling"),
]

MAKES = {
    "Toyota": ["Corolla", "Camry", "RAV4"],
    "Honda": ["Civic", "Accord", "CR-V"],
    "BMW": ["3 Series", "5 Series"],
    "Hyundai": ["Elantra", "Tucson"],
}

# Curated images per part type (Unsplash demo images)
PART_IMAGES = {
    "oil_filter": [
        "https://images.unsplash.com/photo-1542362567-b07e54358753?w=800",
        "https://images.unsplash.com/photo-1511919884226-fd3cad34687c?w=800",
    ],
    "air_filter": [
        "https://images.unsplash.com/photo-1523983388277-336a66bf9bcd?w=800",
    ],
    "cabin_filter": [
        "https://images.unsplash.com/photo-1532635223-7b5d20bbe4b5?w=800",
    ],
    "brake_pads": [
        "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800",
    ],
    "brake_disc": [
        "https://images.unsplash.com/photo-1520975922284-7b14e9a6f208?w=800",
    ],
    "shock_absorber": [
        "https://images.unsplash.com/photo-1518306727298-4c448be9a99a?w=800",
    ],
    "battery": [
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800",
    ],
    "spark_plug": [
        "https://images.unsplash.com/photo-1628543102646-fc5aa0ee33ea?w=800",
    ],
    "timing_belt": [
        "https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=800",
    ],
    "wipers": [
        "https://images.unsplash.com/photo-1617137968427-85924c800a4c?w=800",
    ],
    "fuel_filter": [
        "https://images.unsplash.com/photo-1606229365485-83f69ba4aa64?w=800",
    ],
    "engine_oil": [
        "https://images.unsplash.com/photo-1581091215367-59ab6b514dff?w=800",
    ],
    "starter": [
        "https://images.unsplash.com/photo-1517554558809-9b4971b38f39?w=800",
    ],
    "alternator": [
        "https://images.unsplash.com/photo-1518544801976-3e188bc06147?w=800",
    ],
    "thermostat": [
        "https://images.unsplash.com/photo-1570531492292-4253df3817c5?w=800",
    ],
    "radiator": [
        "https://images.unsplash.com/photo-1592853625600-47d63a9dcc01?w=800",
    ],
}

# Part type catalog: name template, category slug, manufacturer pool, sku prefix, images key
PART_TYPES = [
    ("Масляный фильтр {brand} {code}", "filtry", ["Bosch", "MANN", "Mahle"], "OIL-FLTR", "oil_filter"),
    ("Воздушный фильтр {brand} {code}", "filtry", ["MANN", "Filtron", "Bosch"], "AIR-FLTR", "air_filter"),
    ("Салонный фильтр {brand} {code}", "filtry", ["MANN", "Bosch", "Denso"], "CAB-FLTR", "cabin_filter"),
    ("Тормозные колодки {brand} {code}", "tormoza", ["Brembo", "ATE", "TRW"], "BRK-PADS", "brake_pads"),
    ("Тормозной диск {brand} {code}", "tormoza", ["Brembo", "Zimmermann", "ATE"], "BRK-DISC", "brake_disc"),
    ("Амортизатор {brand} {code}", "podveska", ["KYB", "Sachs", "Monroe"], "AMORT", "shock_absorber"),
    ("Аккумулятор {brand} {code}", "elektrika", ["VARTA", "Bosch", "Exide"], "AKB", "battery"),
    ("Свеча зажигания {brand} {code}", "elektrika", ["NGK", "Denso", "Bosch"], "SPARK", "spark_plug"),
    ("Ремень ГРМ {brand} {code}", "podveska", ["ContiTech", "Gates", "Dayco"], "BELT", "timing_belt"),
    ("Щётки стеклоочистителя {brand} {code}", "elektrika", ["Bosch", "Denso", "Heyner"], "WIPER", "wipers"),
    ("Топливный фильтр {brand} {code}", "filtry", ["Bosch", "Mahle", "MANN"], "FUEL-FLTR", "fuel_filter"),
    ("Моторное масло {brand} {code}", "masla", ["Shell", "Mobil", "Castrol"], "OIL", "engine_oil"),
    ("Стартер {brand} {code}", "elektrika", ["Bosch", "Denso", "Delco"], "STARTER", "starter"),
    ("Генератор {brand} {code}", "elektrika", ["Bosch", "Valeo", "Denso"], "ALT", "alternator"),
    ("Термостат {brand} {code}", "cooling", ["Gates", "Behr", "Mahle"], "THERMO", "thermostat"),
    ("Радиатор охлаждения {brand} {code}", "cooling", ["Denso", "Nissens", "Behr"], "RADIATOR", "radiator"),
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

        # Products: generate realistic names and matching images
        total_created = 0
        total_updated = 0
        for i in range(1, 81):
            part_tpl, category_slug, brands, sku_prefix, img_key = random.choice(PART_TYPES)
            brand = random.choice(brands)
            code = str(100 + i)
            name = part_tpl.format(brand=brand, code=code)
            sku = f"{sku_prefix}-{1000 + i}"
            slug = slugify(f"{name}-{sku}")  # ensure uniqueness

            price = Decimal(random.randint(500, 20000)) / Decimal("1.00")
            in_stock = random.randint(0, 50)
            make = random.choice(list(MAKES.keys()))
            model = random.choice(MAKES[make])
            year = random.choice([2010, 2012, 2015, 2018, 2020, 2022])
            compatibility = [{"make": make, "model": model, "year": year}]
            images = PART_IMAGES.get(img_key) or []

            obj, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "slug": slug,
                    "description": "Учебный товар для демонстрации функций.",
                    "manufacturer": brand,
                    "price": price,
                    "in_stock": in_stock,
                    "images": images,
                    "category": slug_to_cat[category_slug],
                    "compatibility": compatibility,
                },
            )
            if created:
                total_created += 1
            else:
                # Update existing demo product to new realistic data
                obj.name = name
                obj.slug = slug
                obj.manufacturer = brand
                obj.price = price
                obj.in_stock = in_stock
                obj.images = images
                obj.category = slug_to_cat[category_slug]
                obj.compatibility = compatibility
                obj.save()
                total_updated += 1

        # Rename legacy demo products 'Деталь *' to realistic names and images
        legacy_qs = Product.objects.filter(name__startswith="Деталь ")
        legacy_renamed = 0
        for idx, obj in enumerate(legacy_qs, start=1):
            part_tpl, category_slug, brands, sku_prefix, img_key = PART_TYPES[(idx - 1) % len(PART_TYPES)]
            brand = random.choice(brands)
            code = str(500 + idx)
            name = part_tpl.format(brand=brand, code=code)
            obj.name = name
            obj.slug = slugify(f"{name}-{obj.sku}")
            obj.manufacturer = brand
            # Only override images if empty or obviously generic
            new_images = PART_IMAGES.get(img_key) or []
            if new_images:
                obj.images = new_images
            obj.category = slug_to_cat[category_slug]
            obj.save()
            legacy_renamed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Products created: {total_created}; updated: {total_updated}; renamed_legacy: {legacy_renamed}"
            )
        )

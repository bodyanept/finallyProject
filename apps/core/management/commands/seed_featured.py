from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Category, Product


FEATURED = [
    {
        "name": "Масляный фильтр Bosch 0 986 AFL 123",
        "sku": "OIL-FLTR-BOSCH-0123",
        "manufacturer": "Bosch",
        "price": Decimal("890.00"),
        "images": [
            "https://images.unsplash.com/photo-1542362567-b07e54358753?w=800",
            "https://images.unsplash.com/photo-1511919884226-fd3cad34687c?w=800",
        ],
        "category": "filtry",
        "compat": [{"make": "Toyota", "model": "Corolla", "year": 2015}],
        "in_stock": 25,
    },
    {
        "name": "Тормозные колодки Brembo P 85 126",
        "sku": "BRK-BREMBO-P85126",
        "manufacturer": "Brembo",
        "price": Decimal("3450.00"),
        "images": [
            "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800",
        ],
        "category": "tormoza",
        "compat": [{"make": "Honda", "model": "Civic", "year": 2018}],
        "in_stock": 12,
    },
    {
        "name": "Воздушный фильтр Mann C 35 154",
        "sku": "AIR-FLTR-MANN-C35154",
        "manufacturer": "MANN",
        "price": Decimal("1290.00"),
        "images": [
            "https://images.unsplash.com/photo-1523983388277-336a66bf9bcd?w=800",
        ],
        "category": "filtry",
        "compat": [{"make": "Hyundai", "model": "Elantra", "year": 2018}],
        "in_stock": 30,
    },
    {
        "name": "Амортизатор Kayaba Excel-G 341275",
        "sku": "AMORT-KYB-341275",
        "manufacturer": "KYB",
        "price": Decimal("5290.00"),
        "images": [
            "https://images.unsplash.com/photo-1518306727298-4c448be9a99a?w=800",
        ],
        "category": "podveska",
        "compat": [{"make": "Toyota", "model": "RAV4", "year": 2012}],
        "in_stock": 7,
    },
    {
        "name": "Аккумулятор VARTA Blue Dynamic 60Ah",
        "sku": "AKB-VARTA-60",
        "manufacturer": "VARTA",
        "price": Decimal("11990.00"),
        "images": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800",
        ],
        "category": "elektrika",
        "compat": [{"make": "BMW", "model": "3 Series", "year": 2015}],
        "in_stock": 14,
    },
    {
        "name": "Моторное масло 5W-30 Shell Helix HX8 4L",
        "sku": "OIL-SHELL-5W30-4L",
        "manufacturer": "Shell",
        "price": Decimal("2790.00"),
        "images": [
            "https://images.unsplash.com/photo-1581091215367-59ab6b514dff?w=800",
        ],
        "category": "masla",
        "compat": [{"make": "Hyundai", "model": "Tucson", "year": 2020}],
        "in_stock": 40,
    },
]

CATEGORIES = {
    "tormoza": "Тормозная система",
    "filtry": "Фильтры",
    "podveska": "Подвеска",
    "elektrika": "Электрика",
    "masla": "Масла и жидкости",
}


class Command(BaseCommand):
    help = "Seed featured showcase products (curated set)"

    def handle(self, *args, **options):
        # Ensure categories
        slug_to_cat = {}
        for slug, name in CATEGORIES.items():
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            slug_to_cat[slug] = cat

        created = 0
        for item in FEATURED:
            if Product.objects.filter(sku=item["sku"]).exists():
                continue
            Product.objects.create(
                name=item["name"],
                slug=slugify(item["name"]),
                sku=item["sku"],
                description="Демо-позиция для витрины.",
                manufacturer=item["manufacturer"],
                price=item["price"],
                in_stock=item["in_stock"],
                images=item["images"],
                category=slug_to_cat[item["category"]],
                compatibility=item["compat"],
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Featured products created: {created}"))

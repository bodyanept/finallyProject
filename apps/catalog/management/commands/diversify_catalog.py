from __future__ import annotations

import random
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Product, Category, pick_images_for_name


# Pools for diversification
PART_TYPES: List[Tuple[str, str, List[str]]] = [
    # (name template, category slug, brands)
    ("Масляный фильтр {brand} {code}", "filtry", ["Bosch", "MANN", "Mahle", "Filtron", "Denso"]),
    ("Воздушный фильтр {brand} {code}", "filtry", ["MANN", "Filtron", "Bosch", "Mahle"]),
    ("Салонный фильтр {brand} {code}", "filtry", ["MANN", "Bosch", "Denso", "Mahle"]),
    ("Топливный фильтр {brand} {code}", "filtry", ["Bosch", "Mahle", "MANN", "Filtron"]),
    ("Тормозные колодки {brand} {code}", "tormoza", ["Brembo", "ATE", "TRW", "Textar"]),
    ("Тормозной диск {brand} {code}", "tormoza", ["Brembo", "Zimmermann", "ATE", "TRW"]),
    ("Амортизатор {brand} {code}", "podveska", ["KYB", "Sachs", "Monroe", "Bilstein"]),
    ("Ремень ГРМ {brand} {code}", "podveska", ["ContiTech", "Gates", "Dayco"]),
    ("Щётки стеклоочистителя {brand} {code}", "elektrika", ["Bosch", "Denso", "Heyner"]),
    ("Свеча зажигания {brand} {code}", "elektrika", ["NGK", "Denso", "Bosch"]),
    ("Аккумулятор {brand} {code}", "elektrika", ["VARTA", "Bosch", "Exide", "Topla"]),
    ("Стартер {brand} {code}", "elektrika", ["Bosch", "Denso", "Delco"]),
    ("Генератор {brand} {code}", "elektrika", ["Bosch", "Valeo", "Denso"]),
    ("Термостат {brand} {code}", "cooling", ["Gates", "Behr", "Mahle"]),
    ("Радиатор охлаждения {brand} {code}", "cooling", ["Denso", "Nissens", "Behr"]),
]


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = (
        "Diversify existing products without adding new ones: shuffle names/brands/images, "
        "adjust prices and stock. Skus remain intact."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fraction",
            type=float,
            default=0.7,
            help="Fraction of products to modify (0..1). Default: 0.7",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Random seed for reproducible results",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving",
        )
        parser.add_argument(
            "--no-names",
            action="store_true",
            help="Do not change names/manufacturers/categories",
        )
        parser.add_argument(
            "--no-images",
            action="store_true",
            help="Do not change images",
        )
        parser.add_argument(
            "--no-prices",
            action="store_true",
            help="Do not change prices",
        )
        parser.add_argument(
            "--no-stock",
            action="store_true",
            help="Do not change stock",
        )

    def handle(self, *args, **options):
        fraction: float = options["fraction"]
        seed = options.get("seed")
        dry_run: bool = options["dry_run"]
        change_names = not options["no_names"]
        change_images = not options["no_images"]
        change_prices = not options["no_prices"]
        change_stock = not options["no_stock"]

        if seed is not None:
            random.seed(seed)

        # Map categories by slug for quick access
        cats = {c.slug: c for c in Category.objects.all()}

        qs = list(Product.objects.all())
        random.shuffle(qs)
        target_count = int(len(qs) * max(0.0, min(1.0, fraction)))
        target = qs[:target_count]

        updated = 0
        for idx, p in enumerate(target, start=1):
            orig_snapshot = {
                "name": p.name,
                "manufacturer": p.manufacturer,
                "category_id": p.category_id,
                "price": str(p.price),
                "in_stock": p.in_stock,
                "images": list(p.images or []),
            }

            # Names / manufacturers / categories
            if change_names:
                tpl, cat_slug, brands = random.choice(PART_TYPES)
                brand = random.choice(brands)
                code = str(100 + (idx % 900))
                new_name = tpl.format(brand=brand, code=code)
                p.name = new_name
                p.manufacturer = brand
                if cat_slug in cats:
                    p.category = cats[cat_slug]
                # Keep slug unique but stable with sku
                p.slug = slugify(f"{p.name}-{p.sku}")

            # Images to match the (possibly) new name
            if change_images:
                imgs = pick_images_for_name(p.name)
                if imgs:
                    p.images = imgs

            # Prices: random small multiplier within 0.85..1.25
            if change_prices:
                mult = Decimal(str(round(random.uniform(0.85, 1.25), 3)))
                p.price = quantize_money(p.price * mult)

            # Stock: 0..50
            if change_stock:
                p.in_stock = random.randint(0, 50)

            if dry_run:
                # Just show what would change
                self.stdout.write(f"Would update SKU {p.sku}: {orig_snapshot} -> name={p.name}, manuf={p.manufacturer}, cat={p.category.slug if p.category_id else None}, price={p.price}, stock={p.in_stock}, images={p.images[:1]}…")
            else:
                p.save()
                updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run complete. Candidates: {target_count}. No changes saved."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Diversified products updated: {updated} (of {target_count} chosen)"))

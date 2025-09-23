from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.catalog.models import Product, pick_images_for_name


class Command(BaseCommand):
    help = (
        "Refresh product images based on product names using curated internet URLs. "
        "By default, overrides existing images. Use --missing-only to only fill empty."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--missing-only",
            action="store_true",
            help="Only set images for products that currently have no images",
        )
        parser.add_argument(
            "--query",
            type=str,
            default="",
            help="Only process products whose name contains this substring (case-insensitive)",
        )

    def handle(self, *args, **options):
        missing_only: bool = options.get("missing_only", False)
        query: str = (options.get("query") or "").strip()
        updated = 0
        total = 0
        qs = Product.objects.all()
        if query:
            qs = qs.filter(name__icontains=query)
        for p in qs.iterator():
            total += 1
            imgs = pick_images_for_name(p.name)
            if not imgs:
                continue
            if missing_only and p.images:
                continue
            p.images = imgs
            p.save(update_fields=["images"])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Products processed: {total}; images updated: {updated}"))

from decimal import Decimal
import json
from django import forms
from django.contrib import admin
from .models import Category, Product, PriceHistory, ProductChangeLog


class PriceHistoryInline(admin.TabularInline):
    model = PriceHistory
    extra = 0
    readonly_fields = ("old_price", "new_price", "reason", "changed_by", "changed_at")


class ProductChangeLogInline(admin.TabularInline):
    model = ProductChangeLog
    extra = 0
    readonly_fields = ("field", "old_value", "new_value", "changed_by", "changed_at")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "price", "in_stock", "category", "updated_at")
    list_filter = ("category", "manufacturer")
    search_fields = ("name", "sku", "manufacturer", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [PriceHistoryInline, ProductChangeLogInline]

    actions = ["increase_price_10", "decrease_price_10"]

    @admin.action(description="Увеличить цену на 10%%")
    def increase_price_10(self, request, queryset):
        for product in queryset:
            product.price = (product.price * Decimal('1.10')).quantize(Decimal('0.01'))
            product.save()

    @admin.action(description="Уменьшить цену на 10%%")
    def decrease_price_10(self, request, queryset):
        for product in queryset:
            product.price = (product.price * Decimal('0.90')).quantize(Decimal('0.01'))
            product.save()


# --- Custom admin form to make `images` input friendlier ---
class ProductAdminForm(forms.ModelForm):
    # Override JSONField as CharField to accept free-text input; we'll parse it in clean_images
    images = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Вставьте одну ссылку или несколько (через запятую или с новой строки). Также можно вставить корректный JSON: [\"url1\", \"url2\"]",
            }
        ),
    )
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {}

    def clean_images(self):
        value = self.cleaned_data.get("images")
        # If already parsed as list (e.g., coming from programmatic usage), keep it
        if isinstance(value, list):
            # ensure all items are strings
            return [str(v).strip() for v in value if str(v).strip()]
        # If it's a string coming from our Textarea, parse flexibly
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            # Try JSON first if it looks like JSON
            if s.startswith("[") and s.endswith("]"):
                try:
                    data = json.loads(s)
                    if isinstance(data, list):
                        return [str(v).strip() for v in data if str(v).strip()]
                except Exception:
                    pass  # fall back to splitting
            # Fallback: split by commas and newlines
            parts = []
            for line in s.replace("\r", "").split("\n"):
                parts.extend([p.strip() for p in line.split(",")])
            return [p for p in parts if p]
        # Any other type -> empty
        return []


# Attach custom form to admin
ProductAdmin.form = ProductAdminForm


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("product", "old_price", "new_price", "changed_by", "changed_at", "reason")
    list_filter = ("changed_at", "changed_by")
    search_fields = ("product__name", "reason")


@admin.register(ProductChangeLog)
class ProductChangeLogAdmin(admin.ModelAdmin):
    list_display = ("product", "field", "changed_by", "changed_at")
    list_filter = ("field", "changed_at", "changed_by")
    search_fields = ("product__name", "field", "old_value", "new_value")

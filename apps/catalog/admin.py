from decimal import Decimal
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

    @admin.action(description="Увеличить цену на 10%")
    def increase_price_10(self, request, queryset):
        for product in queryset:
            product.price = (product.price * Decimal('1.10')).quantize(Decimal('0.01'))
            product.save()

    @admin.action(description="Уменьшить цену на 10%")
    def decrease_price_10(self, request, queryset):
        for product in queryset:
            product.price = (product.price * Decimal('0.90')).quantize(Decimal('0.01'))
            product.save()


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

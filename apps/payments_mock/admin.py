from django.contrib import admin
from .models import PaymentMock


@admin.register(PaymentMock)
class PaymentMockAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "scenario", "status", "created_at")
    list_filter = ("scenario", "status", "created_at")
    search_fields = ("order__id", "client_secret")

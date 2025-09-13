from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User
from .models import GarageVehicle, Address


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "name", "role", "is_active", "is_staff")
    search_fields = ("email", "name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("name", "balance")} ),
        (_("Permissions"), {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")} ),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    # Use email as the username field
    model = User
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "groups")
    filter_horizontal = ("groups", "user_permissions")


@admin.register(GarageVehicle)
class GarageVehicleAdmin(admin.ModelAdmin):
    list_display = ("user", "make", "model", "year", "vin", "created_at")
    search_fields = ("user__email", "make", "model", "vin")
    list_filter = ("make", "model")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "line1", "postal_code", "phone")
    search_fields = ("user__email", "city", "line1", "postal_code", "phone")

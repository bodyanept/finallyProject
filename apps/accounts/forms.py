from __future__ import annotations

from decimal import Decimal
from django import forms

from .models import User, GarageVehicle, Address


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["line1", "line2", "city", "region", "postal_code", "phone"]
        widgets = {
            "line1": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "line2": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "city": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "region": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "postal_code": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "phone": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
        }


class GarageVehicleForm(forms.ModelForm):
    class Meta:
        model = GarageVehicle
        fields = ["make", "model", "year", "vin"]
        widgets = {
            "make": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "model": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "year": forms.NumberInput(attrs={"class": "w-full rounded-md border px-3 py-2", "min": 1900, "max": 2100}),
            "vin": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
        }


class TopUpForm(forms.Form):
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=12, decimal_places=2,
                                widget=forms.NumberInput(attrs={"class": "w-full rounded-md border px-3 py-2", "step": "0.01"}))

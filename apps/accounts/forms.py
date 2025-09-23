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


class RegisterEmailPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "w-full rounded-md border px-3 py-2"}))
    password = forms.CharField(min_length=6, widget=forms.PasswordInput(attrs={"class": "w-full rounded-md border px-3 py-2"}))
    password2 = forms.CharField(label="Повторите пароль", min_length=6, widget=forms.PasswordInput(attrs={"class": "w-full rounded-md border px-3 py-2"}))

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        pwd2 = cleaned.get("password2")
        if pwd and pwd2 and pwd != pwd2:
            raise forms.ValidationError("Пароли не совпадают")
        return cleaned


class RegisterProfileForm(forms.Form):
    first_name = forms.CharField(label="Имя", max_length=150, widget=forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}))
    last_name = forms.CharField(label="Фамилия", max_length=150, widget=forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}))
    phone = forms.CharField(label="Телефон", max_length=32, widget=forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}))

    def clean_phone(self):
        import re
        phone = self.cleaned_data.get("phone", "").strip()
        # Accept digits, spaces, (), -, +; require at least 10 digits
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Введите корректный номер телефона")
        # Normalize to +7... if starts with 8 and 11 digits (RU common case)
        if len(digits) == 11 and digits.startswith("8"):
            return "+7" + digits[1:]
        if phone.startswith("+"):
            return "+" + digits
        return digits


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "w-full rounded-md border px-3 py-2"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "w-full rounded-md border px-3 py-2"}))


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["line1", "line2", "city", "region", "postal_code"]
        widgets = {
            "line1": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "line2": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "city": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "region": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
            "postal_code": forms.TextInput(attrs={"class": "w-full rounded-md border px-3 py-2"}),
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

    def clean_vin(self):
        import re
        vin = (self.cleaned_data.get("vin") or "").upper().strip()
        if not vin:
            return vin
        if len(vin) != 17:
            raise forms.ValidationError("VIN должен содержать 17 символов")
        if re.search(r"[IOQ]", vin):
            raise forms.ValidationError("VIN не должен содержать I, O или Q")
        if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin):
            raise forms.ValidationError("Некорректный формат VIN")
        return vin


class TopUpForm(forms.Form):
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=12, decimal_places=2,
                                widget=forms.NumberInput(attrs={"class": "w-full rounded-md border px-3 py-2", "step": "0.01"}))

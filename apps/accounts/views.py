from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ProfileForm, GarageVehicleForm, AddressForm, TopUpForm
from .models import GarageVehicle, Address, BalanceTransaction


@login_required
def account_home(request):
    user = request.user

    # Ensure address exists for the user
    addr, _ = Address.objects.get_or_create(user=user)

    # Handle POST actions
    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            form = ProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Профиль обновлён')
                return redirect('/account/')
        elif 'address_submit' in request.POST:
            address_form = AddressForm(request.POST, instance=addr)
            if address_form.is_valid():
                address_form.save()
                messages.success(request, 'Адрес сохранён')
                return redirect('/account/')
        elif 'topup_submit' in request.POST:
            topup_form = TopUpForm(request.POST)
            if topup_form.is_valid():
                amount = topup_form.cleaned_data['amount']
                user.balance = (user.balance + amount)
                user.save()
                BalanceTransaction.objects.create(user=user, amount=amount, type='credit')
                messages.success(request, f'Баланс пополнен на {amount} ₽')
                next_url = request.POST.get('next') or '/account/'
                return redirect(next_url)

    # Initial forms
    form = ProfileForm(instance=user)
    address_form = AddressForm(instance=addr)
    topup_form = TopUpForm()

    garage = user.garage.all()
    garage_form = GarageVehicleForm()
    context = {
        'form': form,
        'address_form': address_form,
        'topup_form': topup_form,
        'garage': garage,
        'garage_form': garage_form,
    }
    return render(request, 'accounts/account.html', context)


@login_required
def garage_add(request):
    if request.method != 'POST':
        return redirect('/account/')
    form = GarageVehicleForm(request.POST)
    if form.is_valid():
        obj: GarageVehicle = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, 'Автомобиль добавлен в гараж')
    else:
        messages.error(request, 'Проверьте поля формы')
    return redirect('/account/')


@login_required
def garage_delete(request, pk: int):
    if request.method != 'POST':
        return redirect('/account/')
    obj = get_object_or_404(GarageVehicle, pk=pk, user=request.user)
    obj.delete()
    messages.success(request, 'Автомобиль удалён')
    return redirect('/account/')

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import (
    ProfileForm,
    GarageVehicleForm,
    AddressForm,
    TopUpForm,
    RegisterEmailPasswordForm,
    RegisterProfileForm,
    LoginForm,
)
from .models import GarageVehicle, Address, BalanceTransaction, User


def _registration_next_step(user) -> str | None:
    """Return URL path of the next required registration step or None if complete."""
    # Step 2: ensure names present
    if not (user.first_name and user.last_name):
        return '/register/step2/'
    # Step 3: ensure address exists and has at least city + line1 + phone
    addr = getattr(user, 'address', None)
    if addr is None or not ((addr.city or '').strip() and (addr.line1 or '').strip() and (addr.phone or '').strip()):
        return '/register/step3/'
    # Step 4: ensure at least one car in garage
    if not user.garage.exists():
        return '/register/step4/'
    return None


@login_required
def account_home(request):
    user = request.user

    # On GET, if registration is incomplete, redirect to next step
    if request.method == 'GET':
        next_step = _registration_next_step(user)
        if next_step:
            return redirect(next_step)

    # Ensure address exists for the forms section
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
    recent_orders = user.orders.all().order_by('-created_at')[:5]
    context = {
        'form': form,
        'address_form': address_form,
        'topup_form': topup_form,
        'garage': garage,
        'garage_form': garage_form,
        'recent_orders': recent_orders,
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


# ---------------------- Registration (multi-step) ----------------------
from django.views.decorators.http import require_http_methods  # noqa: E402


def register_start(request):
    return redirect('/register/step1/')


def login_choice(request):
    """Public page offering a choice to log in or register."""
    if request.user.is_authenticated:
        return redirect('/account/')
    return render(request, 'accounts/login_choice.html')


@require_http_methods(["GET", "POST"])
def login_signin(request):
    """User-facing sign-in form (email + password)."""
    if request.user.is_authenticated:
        return redirect('/account/')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next') or '/account/'
            return redirect(next_url)
        messages.error(request, 'Неверный email или пароль')
    return render(request, 'accounts/login_signin.html', {'form': form})


@require_http_methods(["GET", "POST"])
def register_step1(request):
    """Step 1: email + password. Creates user and logs in, then go to step2."""
    if request.user.is_authenticated:
        return redirect('/register/step2/')
    form = RegisterEmailPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        if User.objects.filter(email=email).exists():
            form.add_error('email', 'Пользователь с таким email уже существует')
        else:
            user = User.objects.create_user(email=email, password=password)
            user.save()
            # authenticate and login
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
            return redirect('/register/step2/')
    return render(request, 'accounts/register_step1.html', {'form': form})


@require_http_methods(["GET", "POST"])
def register_step2(request):
    """Step 2: first_name, last_name, phone (store phone in session until address)."""
    if not request.user.is_authenticated:
        return redirect('/register/step1/')
    form = RegisterProfileForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request.user.first_name = form.cleaned_data['first_name']
        request.user.last_name = form.cleaned_data['last_name']
        # keep combined name for display
        request.user.name = f"{request.user.first_name} {request.user.last_name}".strip()
        request.user.save()
        # store phone temporarily for next step (address)
        request.session['register_phone'] = form.cleaned_data['phone']
        request.session.modified = True
        return redirect('/register/step3/')
    return render(request, 'accounts/register_step2.html', {'form': form})


@require_http_methods(["GET", "POST"])
def register_step3(request):
    """Step 3: address (line1, city, etc). Also set phone from step2."""
    if not request.user.is_authenticated:
        return redirect('/register/step1/')
    addr, _ = Address.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=addr)
        if form.is_valid():
            address = form.save(commit=False)
            if not getattr(address, 'phone', '').strip():
                session_phone = request.session.get('register_phone')
                if session_phone:
                    address.phone = session_phone
            address.user = request.user
            address.save()
            return redirect('/register/step4/')
    else:
        initial = {}
        session_phone = request.session.get('register_phone')
        if session_phone and not getattr(addr, 'phone', '').strip():
            initial['phone'] = session_phone
        form = AddressForm(instance=addr, initial=initial)
    return render(request, 'accounts/register_step3.html', {'form': form})


@require_http_methods(["GET", "POST"])
def register_step4(request):
    """Step 4: car make and model (optional other fields). Finish -> account."""
    if not request.user.is_authenticated:
        return redirect('/register/step1/')
    form = GarageVehicleForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            obj: GarageVehicle = form.save(commit=False)
            obj.user = request.user
            obj.save()
            # cleanup temp session data
            request.session.pop('register_phone', None)
            return redirect('/account/')
        # even if invalid, re-render with errors
        return render(request, 'accounts/register_step4.html', {'form': form})
    # GET
    return render(request, 'accounts/register_step4.html', {'form': form})


# ---------------------- Logout ----------------------
@login_required
def logout_user(request):
    """Logs out the current user and redirects to home page."""
    logout(request)
    return redirect('/')

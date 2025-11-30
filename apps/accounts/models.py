from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifiers."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user using email as username."""

    username = None  # remove username field from AbstractUser
    email = models.EmailField("Адрес электронной почты", unique=True)
    name = models.CharField("Имя", max_length=150, blank=True)
    role = models.CharField(
        "Роль",
        max_length=10,
        choices=(
            ("user", "Пользователь"),
            ("admin", "Администратор"),
        ),
        default="user",
    )
    balance = models.DecimalField("Баланс", max_digits=12, decimal_places=2, default=0)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.email


class BalanceTransaction(models.Model):
    TYPE_CHOICES = (
        ("debit", "Списание"),
        ("credit", "Зачисление"),
    )

    user = models.ForeignKey(
        'accounts.User',
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='balance_transactions',
    )
    order = models.ForeignKey(
        'orders.Order',
        verbose_name='Заказ',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='balance_transactions',
    )
    amount = models.DecimalField("Сумма", max_digits=12, decimal_places=2)
    type = models.CharField("Тип", max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Операция по балансу"
        verbose_name_plural = "Операции по балансу"


    def __str__(self) -> str:  # pragma: no cover - trivial
        sign = '-' if self.type == 'debit' else '+'
        return f"{self.user.email}: {sign}{self.amount} ({self.created_at:%Y-%m-%d})"


class GarageVehicle(models.Model):
    user = models.ForeignKey('accounts.User', verbose_name='Пользователь', on_delete=models.CASCADE, related_name='garage')
    make = models.CharField("Марка", max_length=60)
    model = models.CharField("Модель", max_length=60)
    year = models.PositiveIntegerField("Год", null=True, blank=True)
    vin = models.CharField("VIN", max_length=32, blank=True)
    created_at = models.DateTimeField("Дата добавления", default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"

    def __str__(self) -> str:  # pragma: no cover - trivial
        y = f" {self.year}" if self.year else ""
        return f"{self.make} {self.model}{y}"


class Address(models.Model):
    user = models.OneToOneField('accounts.User', verbose_name='Пользователь', on_delete=models.CASCADE, related_name='address')
    line1 = models.CharField("Адрес", max_length=255, blank=True)
    line2 = models.CharField("Квартира/офис", max_length=255, blank=True)
    city = models.CharField("Город", max_length=120, blank=True)
    region = models.CharField("Регион", max_length=120, blank=True)
    postal_code = models.CharField("Индекс", max_length=20, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.city}, {self.line1}".strip(', ')

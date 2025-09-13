import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()

email = "admin@example.com"
password = "Admin123!"

user, created = User.objects.get_or_create(
    email=email,
    defaults={"is_staff": True, "is_superuser": True, "name": "Admin"},
)
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()
print(f"Admin ensured: {email}")

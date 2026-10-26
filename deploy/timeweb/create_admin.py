"""Create a pilot Django administrator without interactive terminal input."""

import os
import secrets
import sys
from pathlib import Path


repo_root = Path(__file__).resolve().parents[2]
backend_dir = repo_root / "backend"
sys.path.insert(0, str(backend_dir))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command


username = "admin"
password_file = backend_dir / ".admin-initial-password"
if get_user_model().objects.filter(username=username).exists():
    raise SystemExit("Administrator 'admin' already exists; no changes made.")

password = secrets.token_urlsafe(24)
descriptor = os.open(password_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
try:
    with os.fdopen(descriptor, "w", encoding="ascii") as target:
        target.write(password + "\n")
    os.environ["DJANGO_SUPERUSER_PASSWORD"] = password
    call_command("createsuperuser", interactive=False, username=username, email="")
except Exception:
    password_file.unlink(missing_ok=True)
    raise
finally:
    os.environ.pop("DJANGO_SUPERUSER_PASSWORD", None)

print(f"Initial password saved privately in {password_file}")
print("Read it yourself; do not send the password or a screenshot of it.")

"""Create the private Django settings file for a Timeweb pilot deployment."""

import os
import re
import secrets
import sys
from pathlib import Path


def configure(domain, repo_root):
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", domain) or "." not in domain:
        raise ValueError("Pass a hostname only, without https:// or a path.")

    site_dir = repo_root.parent
    public_html = site_dir / "public_html"
    if not public_html.is_dir():
        raise FileNotFoundError(f"Site directory not found: {public_html}")

    destination = repo_root / "backend" / ".env"
    content = "\n".join((
        "DJANGO_DEBUG=false",
        f"DJANGO_SECRET_KEY={secrets.token_urlsafe(48)}",
        f"DJANGO_ALLOWED_HOSTS={domain}",
        "USE_SQLITE=true",
        f"DJANGO_STATIC_ROOT={public_html / 'static'}",
        f"DJANGO_MEDIA_ROOT={public_html / 'media'}",
        "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend",
        "",
    ))
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as target:
        target.write(content)
    print(f"Created private settings: {destination}")
    print("The secret key was generated and was not printed.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python configure.py your-domain.webtm.ru")
    configure(sys.argv[1].strip().lower(), Path(__file__).resolve().parents[2])

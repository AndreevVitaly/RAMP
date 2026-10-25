import hashlib
import json
import secrets
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from .models import AdminContactSettings, CustomerSession

ADMIN_TOKEN_SALT = "ramp-admin-session"


def normalize_phone(value):
    digits = "".join(character for character in str(value) if character.isdigit())
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) < 10 or len(digits) > 15:
        raise ValueError("Укажите корректный номер телефона.")
    return "+" + digits


def digest(value):
    return hashlib.sha256(f"{settings.SECRET_KEY}:{value}".encode()).hexdigest()


def customer_from_request(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise AuthenticationFailed("Войдите в личный кабинет.")
    session = CustomerSession.objects.select_related("customer").filter(
        token_digest=digest(header[7:]), expires_at__gt=timezone.now()
    ).first()
    if not session:
        raise AuthenticationFailed("Сессия истекла. Войдите снова.")
    return session.customer


def issue_session(customer):
    token = secrets.token_urlsafe(32)
    CustomerSession.objects.create(customer=customer, token_digest=digest(token), expires_at=timezone.now() + timedelta(days=30))
    return token


def issue_admin_token(user):
    return TimestampSigner(salt=ADMIN_TOKEN_SALT).sign(f"{user.pk}:{user.get_session_auth_hash()}")


def admin_authorized(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False
    try:
        value = TimestampSigner(salt=ADMIN_TOKEN_SALT).unsign(header[7:], max_age=60 * 60 * 12)
        user_id, password_hash = value.split(":", 1)
        user = get_user_model().objects.filter(pk=user_id, is_active=True, is_staff=True).first()
        return bool(user and secrets.compare_digest(password_hash, user.get_session_auth_hash()))
    except (BadSignature, SignatureExpired, ValueError):
        return False


def send_sms_code(phone, code):
    if not settings.SMS_PROVIDER_URL:
        return False
    request = urllib.request.Request(
        settings.SMS_PROVIDER_URL,
        data=json.dumps({"phone": phone, "message": f"Код входа RAMP: {code}"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.SMS_API_KEY}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10):
        return True


def deliver_brief(brief):
    contacts = AdminContactSettings.objects.first() or AdminContactSettings()
    customer = brief.customer
    summary = (
        f"Новое техническое задание RAMP №{brief.pk}\n"
        f"Клиент: {customer.name}\nТелефон: {customer.phone or 'не указан'}\nEmail: {customer.email}\n\n"
        f"Комментарий: {brief.message or '—'}\n\nКонфигурация:\n{json.dumps(brief.configuration, ensure_ascii=False, indent=2)}"
    )
    status = {}
    for channel in brief.requested_channels:
        try:
            if channel == "email" and contacts.email:
                send_mail(f"Техническое задание RAMP №{brief.pk}", summary, settings.DEFAULT_FROM_EMAIL, [contacts.email])
            elif channel == "telegram" and settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                request = urllib.request.Request(url, data=json.dumps({"chat_id": settings.TELEGRAM_CHAT_ID, "text": summary}).encode(), headers={"Content-Type": "application/json"})
                urllib.request.urlopen(request, timeout=10).close()
            elif channel == "max" and settings.MAX_API_URL and settings.MAX_API_TOKEN:
                request = urllib.request.Request(settings.MAX_API_URL, data=json.dumps({"text": summary}).encode(), headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.MAX_API_TOKEN}"})
                urllib.request.urlopen(request, timeout=10).close()
            else:
                status[channel] = "not_configured"
                continue
            status[channel] = "sent"
        except Exception:
            status[channel] = "failed"
    brief.delivery_status = status
    brief.save(update_fields=("delivery_status",))
    return status

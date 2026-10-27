from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .accounts import digest
from .models import CustomerAuthAttempt, EmailCodeRequest


def allow_email_code_request(request, email):
    """Apply shared database limits across registration and login code requests."""
    now = timezone.now()
    hour_ago = now - timedelta(hours=1)
    EmailCodeRequest.objects.filter(created_at__lt=now - timedelta(days=1)).delete()
    email_digest = digest(f"email:{email.strip().lower()}")
    ip_digest = digest(f"ip:{request.META.get('REMOTE_ADDR', '')}")
    recent = EmailCodeRequest.objects.filter(created_at__gte=hour_ago)
    email_requests = recent.filter(email_digest=email_digest)
    last = email_requests.order_by("-created_at").first()
    if last and (now - last.created_at).total_seconds() < settings.EMAIL_CODE_COOLDOWN_SECONDS:
        return False
    if email_requests.count() >= settings.EMAIL_CODE_EMAIL_HOURLY_LIMIT:
        return False
    if recent.filter(ip_digest=ip_digest).count() >= settings.EMAIL_CODE_IP_HOURLY_LIMIT:
        return False
    EmailCodeRequest.objects.create(email_digest=email_digest, ip_digest=ip_digest)
    return True


def allow_customer_auth_attempt(request, email, purpose):
    now = timezone.now()
    CustomerAuthAttempt.objects.filter(created_at__lt=now - timedelta(days=1)).delete()
    recent = CustomerAuthAttempt.objects.filter(purpose=purpose, created_at__gte=now - timedelta(hours=1))
    email_digest = digest(f"email:{email.strip().lower()}")
    ip_digest = digest(f"ip:{request.META.get('REMOTE_ADDR', '')}")
    email_limit, ip_limit = (10, 50) if purpose == "login" else (3, 10)
    if recent.filter(email_digest=email_digest).count() >= email_limit:
        return False
    if recent.filter(ip_digest=ip_digest).count() >= ip_limit:
        return False
    CustomerAuthAttempt.objects.create(purpose=purpose, email_digest=email_digest, ip_digest=ip_digest)
    return True

import uuid

from django.db import models


def image_upload_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"ramp_images/{instance.kind}/{uuid.uuid4().hex}.{extension}"


class RampImage(models.Model):
    PHOTO = "photo"
    ILLUSTRATION = "illustration"
    KIND_CHOICES = ((PHOTO, "Фотография"), (ILLUSTRATION, "Иллюстрация"))
    IMAGE_TYPE_CHOICES = (
        ("product", "Главный вид изделия"),
        ("sofa", "Пандус возле дивана"),
        ("bed", "Пандус возле кровати"),
        ("folded", "Пандус в сложенном состоянии"),
        ("storage", "Хранение за мебелью"),
        ("carpet", "Крупный план покрытия"),
    )

    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    file = models.FileField(upload_to=image_upload_path)
    original_name = models.CharField(max_length=255)
    file_sha256 = models.CharField(max_length=64)
    title = models.CharField(max_length=160, blank=True)
    caption = models.CharField(max_length=300, blank=True)
    image_type = models.CharField(max_length=30, choices=IMAGE_TYPE_CHOICES, blank=True)
    color = models.CharField(max_length=30, blank=True)
    has_slats = models.BooleanField(default=True)
    side_rails = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-is_primary", "-created_at")


class AdminContactSettings(models.Model):
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    telegram = models.CharField(max_length=80, blank=True)
    max_contact = models.CharField(max_length=160, blank=True)
    preferred_channel = models.CharField(max_length=20, default="email")
    updated_at = models.DateTimeField(auto_now=True)


class Customer(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, unique=True)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PhoneVerification(models.Model):
    phone = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    code_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class CustomerSession(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="sessions")
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class TechnicalBrief(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="technical_briefs")
    message = models.TextField(blank=True)
    configuration = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    requested_channels = models.JSONField(default=list)
    delivery_status = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


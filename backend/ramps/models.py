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


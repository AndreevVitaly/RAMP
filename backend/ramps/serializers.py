import hashlib
import json
from pathlib import Path

from rest_framework import serializers

from .models import AdminContactSettings, Customer, RampImage, TechnicalBrief
from .services import (
    ALLOWED_COLORS,
    DEFAULT_COLOR,
    DEFAULT_SUPPORT_PANEL_WIDTH_CM,
    DEFAULT_WIDTH_CM,
)


class RampCalculationSerializer(serializers.Serializer):
    height_cm = serializers.FloatField()
    ramp_length_cm = serializers.FloatField(required=False)
    width_cm = serializers.FloatField(required=False, default=DEFAULT_WIDTH_CM)
    support_panel_width_cm = serializers.FloatField(required=False, default=DEFAULT_SUPPORT_PANEL_WIDTH_CM)
    color = serializers.ChoiceField(required=False, default=DEFAULT_COLOR, choices=ALLOWED_COLORS)
    has_slats = serializers.BooleanField(required=False, default=True)
    product_state = serializers.ChoiceField(required=False, default="deployed", choices=("deployed", "folded"))
    side_rails = serializers.BooleanField(required=False, default=False)


class RampImageSerializer(serializers.ModelSerializer):
    is_illustration = serializers.SerializerMethodField()

    class Meta:
        model = RampImage
        fields = (
            "id", "kind", "file", "original_name", "file_sha256", "title", "caption",
            "image_type", "color", "has_slats", "side_rails", "description", "configuration",
            "is_primary", "is_illustration", "created_at",
        )
        read_only_fields = ("original_name", "file_sha256", "is_illustration", "created_at")

    def get_is_illustration(self, obj):
        return obj.kind == RampImage.ILLUSTRATION

    def validate_file(self, value):
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if Path(value.name).suffix.lower() not in allowed_extensions or value.content_type not in allowed_types:
            raise serializers.ValidationError("Поддерживаются только JPG, PNG и WebP.")
        return value

    def validate_configuration(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as error:
                raise serializers.ValidationError("Некорректная конфигурация изделия.") from error
        return value

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        if kind == RampImage.ILLUSTRATION and not attrs.get("image_type", getattr(self.instance, "image_type", "")):
            raise serializers.ValidationError({"image_type": "Укажите тип иллюстрации."})
        return attrs

    def create(self, validated_data):
        uploaded = validated_data["file"]
        digest = hashlib.sha256()
        for chunk in uploaded.chunks():
            digest.update(chunk)
        uploaded.seek(0)
        validated_data["original_name"] = uploaded.name
        validated_data["file_sha256"] = digest.hexdigest()
        if validated_data.get("is_primary"):
            RampImage.objects.update(is_primary=False)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_primary"):
            RampImage.objects.exclude(pk=instance.pk).update(is_primary=False)
        return super().update(instance, validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "phone_verified", "created_at")
        read_only_fields = fields


class AdminContactSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminContactSettings
        fields = ("email", "phone", "telegram", "max_contact", "preferred_channel", "updated_at")
        read_only_fields = ("updated_at",)


class TechnicalBriefSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = TechnicalBrief
        fields = ("id", "customer", "message", "configuration", "result", "requested_channels", "delivery_status", "created_at")
        read_only_fields = ("id", "customer", "delivery_status", "created_at")

    def validate_requested_channels(self, value):
        allowed = {"email", "telegram", "max"}
        if not value or any(item not in allowed for item in value):
            raise serializers.ValidationError("Выберите хотя бы один доступный канал отправки.")
        return list(dict.fromkeys(value))


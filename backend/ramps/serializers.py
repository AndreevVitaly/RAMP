import hashlib
import json
from pathlib import Path

from rest_framework import serializers

from .models import AdminContactSettings, Customer, RampImage, SavedProject, TechnicalBrief
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
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Размер изображения не должен превышать 10 МБ.")
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
    has_password = serializers.SerializerMethodField()

    def get_has_password(self, customer):
        return bool(customer.password_hash)

    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "email_verified", "has_password", "created_at")
        read_only_fields = fields


class SavedProjectSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)

    class Meta:
        model = SavedProject
        fields = ("id", "name", "configuration", "status", "planned_completion_date", "selected_by_admin", "completed_at", "created_at", "updated_at")
        read_only_fields = ("id", "status", "planned_completion_date", "selected_by_admin", "completed_at", "created_at", "updated_at")

    def validate_configuration(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Передайте параметры изделия.")
        product = {key: value[key] for key in RampCalculationSerializer().fields if key in value}
        calculation = RampCalculationSerializer(data=product)
        calculation.is_valid(raise_exception=True)
        from .services import RampGeometryError, calculate_ramp_configuration

        try:
            result = calculate_ramp_configuration(**calculation.validated_data)
        except RampGeometryError as error:
            raise serializers.ValidationError(str(error)) from error

        pet = value.get("pet")
        if pet is not None:
            breeds = {"dachshund", "corgi", "pomeranian", "beagle", "french_bulldog", "labrador", "german_shepherd"}
            if not isinstance(pet, dict) or pet.get("breed") not in breeds or not isinstance(pet.get("enabled"), bool):
                raise serializers.ValidationError("Укажите доступную породу питомца.")
        return {**calculation.validated_data, "ramp_length_cm": result["ramp_length_cm"], **({"pet": {"breed": pet["breed"], "enabled": pet["enabled"]}} if pet else {})}

    def create(self, validated_data):
        if not validated_data.get("name"):
            configuration = validated_data["configuration"]
            validated_data["name"] = f"Пандус {configuration['height_cm']:g} × {configuration['ramp_length_cm']:g} см"
        return super().create(validated_data)


class AdminSavedProjectSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = SavedProject
        fields = ("id", "name", "customer", "configuration", "status", "planned_completion_date", "selected_by_admin", "completed_at", "created_at", "updated_at")
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


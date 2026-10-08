from rest_framework import serializers
from .services import (
    ALLOWED_COLORS,
    DEFAULT_COLOR,
    DEFAULT_SUPPORT_PANEL_VISUAL_THICKNESS_CM,
    DEFAULT_SUPPORT_PANEL_WIDTH_CM,
    DEFAULT_WIDTH_CM,
)


class RampCalculationSerializer(serializers.Serializer):
    height_cm = serializers.FloatField()
    ramp_length_cm = serializers.FloatField(required=False)
    width_cm = serializers.FloatField(required=False, default=DEFAULT_WIDTH_CM)
    support_panel_width_cm = serializers.FloatField(required=False, default=DEFAULT_SUPPORT_PANEL_WIDTH_CM)
    support_panel_visual_thickness_cm = serializers.FloatField(required=False, default=DEFAULT_SUPPORT_PANEL_VISUAL_THICKNESS_CM)
    color = serializers.ChoiceField(required=False, default=DEFAULT_COLOR, choices=ALLOWED_COLORS)
    side_rails = serializers.BooleanField(required=False, default=False)


from dataclasses import asdict, dataclass
from math import cos, hypot, radians, sin, sqrt

BASE_VERTICAL_OFFSET_CM = 5.0
SUPPORT_FLOOR_ANGLE_DEG = 105.0
# Backward-compatible name used by the existing API.
SUPPORT_BASE_ANGLE_DEG = SUPPORT_FLOOR_ANGLE_DEG
SUPPORT_FOLD_DIRECTION = "inward"
SUPPORT_DEPLOYED_STATE = "deployed"
SUPPORT_HINGE_COUNT = 2


class RampGeometryError(ValueError):
    """Конфигурация не позволяет построить физически корректный профиль."""


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def to_dict(self) -> dict[str, float]:
        return {key: round(value, 4) for key, value in asdict(self).items()}


def point_on_ramp(distance_cm: float, ramp_length_cm: float, ramp_end: Point) -> Point:
    ratio = distance_cm / ramp_length_cm
    return Point(x=ratio * ramp_end.x, y=ratio * ramp_end.y)


def build_side_profile(
    *, height_cm: float, ramp_length_cm: float, step_positions_cm: list[float]
) -> dict:
    if height_cm <= 0:
        raise RampGeometryError("Высота должна быть больше 0 см.")
    if ramp_length_cm <= 0:
        raise RampGeometryError("Длина пандуса должна быть больше 0 см.")
    if height_cm >= ramp_length_cm:
        raise RampGeometryError("Длина наклонной поверхности должна быть больше высоты.")

    horizontal_run = sqrt(ramp_length_cm**2 - height_cm**2)
    base_length = horizontal_run - BASE_VERTICAL_OFFSET_CM
    if base_length <= 0:
        raise RampGeometryError(
            "Горизонтальная проекция слишком мала для основания с отступом 5 см."
        )

    ramp_start = Point(0.0, 0.0)  # A
    ramp_end = Point(horizontal_run, height_cm)  # B
    vertical_projection = Point(horizontal_run, 0.0)  # V
    base_end = Point(base_length, 0.0)  # C

    legacy_support_angle_rad = radians(SUPPORT_FLOOR_ANGLE_DEG)
    legacy_support_dx = cos(legacy_support_angle_rad)
    legacy_support_dy = sin(legacy_support_angle_rad)
    ramp_slope = height_cm / horizontal_run

    # Preserve the established hinge D on the ramp. The old support line was
    # used only to locate this hinge; C is no longer the support foot.
    denominator = legacy_support_dy - ramp_slope * legacy_support_dx
    if abs(denominator) < 1e-9:
        raise RampGeometryError("Опорная стойка параллельна рабочей поверхности.")
    legacy_distance = ramp_slope * base_end.x / denominator
    intersection = Point(
        x=base_end.x + legacy_distance * legacy_support_dx,
        y=legacy_distance * legacy_support_dy,
    )  # D

    ramp_parameter = intersection.x / horizontal_run
    if legacy_distance <= 0 or not 0 < ramp_parameter < 1:
        raise RampGeometryError(
            "Опорная стойка не пересекает рабочую поверхность внутри конструкции."
        )

    # The physical S→D vector must point up and right. The specified 105° is
    # the obtuse angle to the floor, so its +X direction is the supplement 75°.
    support_direction_deg = 180.0 - SUPPORT_FLOOR_ANGLE_DEG
    support_direction_rad = radians(support_direction_deg)
    support_length = intersection.y / sin(support_direction_rad)
    support_foot = Point(
        x=intersection.x - support_length * cos(support_direction_rad),
        y=0.0,
    )  # S
    if not 0 < support_foot.x < base_end.x or support_foot.x >= intersection.x:
        raise RampGeometryError(
            "Нижний конец опорной стойки не помещается внутри основания."
        )

    step_points = [
        {
            "distance_cm": round(position, 4),
            **point_on_ramp(position, ramp_length_cm, ramp_end).to_dict(),
        }
        for position in step_positions_cm
    ]

    hinge_point = intersection.to_dict()
    contact_point = support_foot.to_dict()
    support = {
        "type": "folding",
        "state": SUPPORT_DEPLOYED_STATE,
        "hinged": True,
        "fold_direction": SUPPORT_FOLD_DIRECTION,
        "base_angle_deg": SUPPORT_FLOOR_ANGLE_DEG,
        "floor_angle_deg": SUPPORT_FLOOR_ANGLE_DEG,
        "direction_from_positive_x_deg": support_direction_deg,
        "length_cm": round(support_length, 4),
        "upper_connection": {
            "type": "hinge",
            "point": hinge_point,
            "hinge_count": SUPPORT_HINGE_COUNT,
        },
        "lower_connection": {
            "type": "free_contact",
            "point": contact_point,
            "hinged": False,
            "rests_on": "support_stop",
        },
    }

    return {
        "points": {
            "ramp_start": ramp_start.to_dict(),
            "ramp_end": ramp_end.to_dict(),
            "vertical_projection": vertical_projection.to_dict(),
            "base_end": base_end.to_dict(),
            "support_ramp_intersection": intersection.to_dict(),
            "support_hinge": intersection.to_dict(),
            "support_foot": support_foot.to_dict(),
        },
        "base_length_cm": round(base_length, 4),
        "base_vertical_offset_cm": BASE_VERTICAL_OFFSET_CM,
        "support_base_angle_deg": SUPPORT_FLOOR_ANGLE_DEG,
        "support_floor_angle_deg": SUPPORT_FLOOR_ANGLE_DEG,
        "support_foot_to_base_end_cm": round(base_end.x - support_foot.x, 4),
        "support_length_cm": round(
            hypot(intersection.x - base_end.x, intersection.y - base_end.y), 4
        ),
        "step_points": step_points,
        "support": support,
        "support_hinge": {
            "type": "rotation_axis",
            "point": hinge_point,
            "hinge_count": SUPPORT_HINGE_COUNT,
            "connects": ["ramp_surface", "support"],
        },
        "support_stop": {
            "type": "mechanical_stop",
            "purpose": "support_lower_end_stop",
            "contact_point": contact_point,
            "mounted_on": "base",
            "dimensions_defined": False,
        },
    }


from dataclasses import asdict, dataclass
from math import cos, hypot, radians, sin, sqrt

BASE_VERTICAL_OFFSET_CM = 5.0
SUPPORT_BASE_ANGLE_DEG = 105.0
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

    support_angle_rad = radians(SUPPORT_BASE_ANGLE_DEG)
    support_dx = cos(support_angle_rad)
    support_dy = sin(support_angle_rad)
    ramp_slope = height_cm / horizontal_run

    # C + u*(cos(105°), sin(105°)) intersects the ramp line y = ramp_slope*x.
    denominator = support_dy - ramp_slope * support_dx
    if abs(denominator) < 1e-9:
        raise RampGeometryError("Опорная стойка параллельна рабочей поверхности.")
    support_length = ramp_slope * base_end.x / denominator
    intersection = Point(
        x=base_end.x + support_length * support_dx,
        y=support_length * support_dy,
    )  # D

    ramp_parameter = intersection.x / horizontal_run
    if support_length <= 0 or not 0 < ramp_parameter < 1:
        raise RampGeometryError(
            "Опорная стойка не пересекает рабочую поверхность внутри конструкции."
        )

    step_points = [
        {
            "distance_cm": round(position, 4),
            **point_on_ramp(position, ramp_length_cm, ramp_end).to_dict(),
        }
        for position in step_positions_cm
    ]

    hinge_point = intersection.to_dict()
    contact_point = base_end.to_dict()
    support = {
        "type": "folding",
        "state": SUPPORT_DEPLOYED_STATE,
        "hinged": True,
        "fold_direction": SUPPORT_FOLD_DIRECTION,
        "base_angle_deg": SUPPORT_BASE_ANGLE_DEG,
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
        },
        "base_length_cm": round(base_length, 4),
        "base_vertical_offset_cm": BASE_VERTICAL_OFFSET_CM,
        "support_base_angle_deg": SUPPORT_BASE_ANGLE_DEG,
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


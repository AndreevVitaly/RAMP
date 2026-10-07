from dataclasses import asdict, dataclass
from math import cos, hypot, radians, sin, sqrt

BASE_VERTICAL_OFFSET_CM = 5.0
SUPPORT_FLOOR_ANGLE_DEG = 105.0
SUPPORT_HINGE_POSITION_RATIO = 0.75
# Backward-compatible name used by the existing API.
SUPPORT_BASE_ANGLE_DEG = SUPPORT_FLOOR_ANGLE_DEG
SUPPORT_FOLD_DIRECTION = "inward"
SUPPORT_DEPLOYED_STATE = "deployed"
SUPPORT_HINGE_COUNT = 2
STEP_WIDTH_CM = 3.0


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

    hinge_distance = ramp_length_cm * SUPPORT_HINGE_POSITION_RATIO
    intersection = point_on_ramp(hinge_distance, ramp_length_cm, ramp_end)  # D

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

    step_points = []
    for position in step_positions_cm:
        end_position = position + STEP_WIDTH_CM
        start_point = point_on_ramp(position, ramp_length_cm, ramp_end)
        end_point = point_on_ramp(end_position, ramp_length_cm, ramp_end)
        step_points.append(
            {
                "start_distance_cm": round(position, 4),
                "end_distance_cm": round(end_position, 4),
                "width_cm": STEP_WIDTH_CM,
                "start": start_point.to_dict(),
                "end": end_point.to_dict(),
                # Start coordinate aliases keep older API consumers functional.
                "distance_cm": round(position, 4),
                **start_point.to_dict(),
            }
        )

    hinge_point = intersection.to_dict()
    contact_point = support_foot.to_dict()
    support = {
        "type": "folding",
        "folding": True,
        "state": SUPPORT_DEPLOYED_STATE,
        "hinged": True,
        "fold_direction": SUPPORT_FOLD_DIRECTION,
        "base_angle_deg": SUPPORT_FLOOR_ANGLE_DEG,
        "floor_angle_deg": SUPPORT_FLOOR_ANGLE_DEG,
        "direction_from_positive_x_deg": support_direction_deg,
        "hinge_position_ratio": SUPPORT_HINGE_POSITION_RATIO,
        "hinge_distance_cm": round(hinge_distance, 4),
        "hinge": hinge_point,
        "foot": contact_point,
        "hinge_count": SUPPORT_HINGE_COUNT,
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
        "measurements": {
            "ramp_start_to_hinge_cm": round(hinge_distance, 4),
            "ramp_start_to_support_foot_cm": round(support_foot.x, 4),
            "support_foot_to_base_end_cm": round(base_end.x - support_foot.x, 4),
            "support_length_cm": round(support_length, 4),
        },
        "support_length_cm": round(
            hypot(intersection.x - support_foot.x, intersection.y - support_foot.y), 4
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


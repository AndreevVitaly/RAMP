from dataclasses import asdict, dataclass
from math import cos, radians, sin

SIDE_RAIL_HEIGHT_CM = 5.0


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float

    def to_dict(self) -> dict[str, float]:
        return {key: round(value, 4) for key, value in asdict(self).items()}


def build_ramp_geometry_3d(
    *,
    height_cm: float,
    ramp_length_cm: float,
    width_cm: float,
    angle_deg: float,
    horizontal_run_cm: float,
    base_length_cm: float,
    step_points: list[dict],
    support_hinge: dict,
    support_foot: dict,
    side_rails_enabled: bool,
) -> dict:
    """Extrude the authoritative X/Z side profile across parameterized Y width."""
    center_y = width_cm / 2

    def point(x, y, z):
        return Point3D(x, y, z).to_dict()

    ramp_surface = {
        "length_cm": round(ramp_length_cm, 4),
        "width_cm": round(width_cm, 4),
        "angle_deg": angle_deg,
        "corners": {
            "a_left": point(0, 0, 0),
            "a_right": point(0, width_cm, 0),
            "b_left": point(horizontal_run_cm, 0, height_cm),
            "b_right": point(horizontal_run_cm, width_cm, height_cm),
        },
    }
    base = {
        "length_cm": round(base_length_cm, 4),
        "width_cm": round(width_cm, 4),
        "corners": {
            "a_left": point(0, 0, 0),
            "a_right": point(0, width_cm, 0),
            "c_left": point(base_length_cm, 0, 0),
            "c_right": point(base_length_cm, width_cm, 0),
        },
    }
    steps = [
        {
            "start_distance_cm": step["start_distance_cm"],
            "end_distance_cm": step["end_distance_cm"],
            "width_cm": step["width_cm"],
            "start_left": point(step["start"]["x"], 0, step["start"]["y"]),
            "start_right": point(step["start"]["x"], width_cm, step["start"]["y"]),
            "end_left": point(step["end"]["x"], 0, step["end"]["y"]),
            "end_right": point(step["end"]["x"], width_cm, step["end"]["y"]),
        }
        for step in step_points
    ]
    hinge_center = point(support_hinge["x"], center_y, support_hinge["y"])
    foot_center = point(support_foot["x"], center_y, support_foot["y"])
    side_rails = {"enabled": False, "count": 0}
    if side_rails_enabled:
        angle_rad = radians(angle_deg)
        normal_x = -sin(angle_rad)
        normal_z = cos(angle_rad)

        def rail_at(y):
            return {
                "bottom_start": point(0, y, 0),
                "bottom_end": point(horizontal_run_cm, y, height_cm),
                "top_start": point(SIDE_RAIL_HEIGHT_CM * normal_x, y, SIDE_RAIL_HEIGHT_CM * normal_z),
                "top_end": point(horizontal_run_cm + SIDE_RAIL_HEIGHT_CM * normal_x, y, height_cm + SIDE_RAIL_HEIGHT_CM * normal_z),
            }

        area = ramp_length_cm * SIDE_RAIL_HEIGHT_CM
        side_rails = {
            "enabled": True,
            "count": 2,
            "height_cm": SIDE_RAIL_HEIGHT_CM,
            "length_cm": round(ramp_length_cm, 4),
            "area_each_cm2": round(area, 4),
            "area_total_cm2": round(area * 2, 4),
            "thickness_defined": False,
            "normal_xz": {"x": round(normal_x, 6), "z": round(normal_z, 6)},
            "left": rail_at(0),
            "right": rail_at(width_cm),
        }
    return {
        "coordinate_system": {
            "origin": "ramp_start",
            "x": "horizontal_run",
            "y": "width",
            "z": "height",
            "units": "cm",
        },
        "dimensions": {
            "height_cm": round(height_cm, 4),
            "ramp_length_cm": round(ramp_length_cm, 4),
            "horizontal_run_cm": round(horizontal_run_cm, 4),
            "base_length_cm": round(base_length_cm, 4),
            "width_cm": round(width_cm, 4),
        },
        "ramp_surface": ramp_surface,
        "base": base,
        "steps": steps,
        "support": {
            "axis": {"hinge": hinge_center, "foot": foot_center},
            "center_y_cm": round(center_y, 4),
            "cross_section_defined": False,
        },
        "hinge_axis": {
            "center": hinge_center,
            "left": point(support_hinge["x"], 0, support_hinge["y"]),
            "right": point(support_hinge["x"], width_cm, support_hinge["y"]),
            "hinge_count": 2,
            "hinge_positions_y_defined": False,
        },
        "support_stop": {
            "contact_center": foot_center,
            "left": point(support_foot["x"], 0, 0),
            "right": point(support_foot["x"], width_cm, 0),
            "dimensions_defined": False,
            "display_note": "Схематично — размеры не определены",
        },
        "side_rails": side_rails,
    }


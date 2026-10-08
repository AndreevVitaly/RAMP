from dataclasses import asdict, dataclass
from math import cos, radians, sin


SIDE_PANEL_HEIGHT_CM = 5.0


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
    support_panel_width_cm: float,
    support_panel_visual_thickness_cm: float,
    finished_panel_thickness_cm: float,
    product_state: str,
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
    angle_rad = radians(angle_deg)
    surface_normal_x = -sin(angle_rad)
    surface_normal_z = cos(angle_rad)

    def below_surface(p):
        return point(
            p["x"] - finished_panel_thickness_cm * surface_normal_x,
            p["y"],
            p["z"] - finished_panel_thickness_cm * surface_normal_z,
        )

    ramp_surface["finished_thickness_cm"] = round(finished_panel_thickness_cm, 4)
    ramp_surface["plywood_thickness_cm"] = 0.8
    ramp_surface["carpet_thickness_cm"] = 0.2
    ramp_surface["volume_corners"] = {
        **{f"top_{name}": value for name, value in ramp_surface["corners"].items()},
        **{f"bottom_{name}": below_surface(value) for name, value in ramp_surface["corners"].items()},
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
    base["finished_thickness_cm"] = round(finished_panel_thickness_cm, 4)
    base["volume_corners"] = {
        **{f"top_{name}": value for name, value in base["corners"].items()},
        **{f"bottom_{name}": point(value["x"], value["y"], value["z"] - finished_panel_thickness_cm) for name, value in base["corners"].items()},
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
    support_dx = support_hinge["x"] - support_foot["x"]
    support_dz = support_hinge["y"] - support_foot["y"]
    support_length = (support_dx**2 + support_dz**2) ** 0.5
    support_normal_x = -support_dz / support_length
    support_normal_z = support_dx / support_length
    half_support_width = support_panel_width_cm / 2
    half_visual_thickness = support_panel_visual_thickness_cm / 2
    support_y_min = center_y - half_support_width
    support_y_max = center_y + half_support_width

    def support_corner(endpoint, y, thickness_side):
        offset = half_visual_thickness * thickness_side
        return point(
            endpoint["x"] + support_normal_x * offset,
            y,
            endpoint["y"] + support_normal_z * offset,
        )

    support_panel_corners = {
        "foot_left_front": support_corner(support_foot, support_y_min, 1),
        "foot_right_front": support_corner(support_foot, support_y_max, 1),
        "hinge_left_front": support_corner(support_hinge, support_y_min, 1),
        "hinge_right_front": support_corner(support_hinge, support_y_max, 1),
        "foot_left_back": support_corner(support_foot, support_y_min, -1),
        "foot_right_back": support_corner(support_foot, support_y_max, -1),
        "hinge_left_back": support_corner(support_hinge, support_y_min, -1),
        "hinge_right_back": support_corner(support_hinge, support_y_max, -1),
    }
    side_panels = {"enabled": False, "count": 0}
    if side_rails_enabled:
        angle_rad = radians(angle_deg)
        normal_x = -sin(angle_rad)
        normal_z = cos(angle_rad)

        def panel_at(y):
            bottom_start = point(0, y, 0)
            bottom_end = point(horizontal_run_cm, y, height_cm)
            return {
                "bottom_start": bottom_start,
                "bottom_end": bottom_end,
                "top_start": point(
                    SIDE_PANEL_HEIGHT_CM * normal_x,
                    y,
                    SIDE_PANEL_HEIGHT_CM * normal_z,
                ),
                "top_end": point(
                    horizontal_run_cm + SIDE_PANEL_HEIGHT_CM * normal_x,
                    y,
                    height_cm + SIDE_PANEL_HEIGHT_CM * normal_z,
                ),
            }

        area_each = ramp_length_cm * SIDE_PANEL_HEIGHT_CM
        side_panels = {
            "enabled": True,
            "count": 2,
            "length_cm": round(ramp_length_cm, 4),
            "height_cm": SIDE_PANEL_HEIGHT_CM,
            "area_each_one_side_cm2": round(area_each, 4),
            "area_total_one_side_cm2": round(area_each * 2, 4),
            "thickness_defined": False,
            "surface_normal": {"x": round(normal_x, 6), "y": 0, "z": round(normal_z, 6)},
            "left": panel_at(0),
            "right": panel_at(width_cm),
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
            "length_cm": round(support_length, 4),
            "panel_width_cm": round(support_panel_width_cm, 4),
            "available_inner_width_cm": round(width_cm, 4),
            "y_min_cm": round(support_y_min, 4),
            "y_max_cm": round(support_y_max, 4),
            "thickness_cm": round(support_panel_visual_thickness_cm, 4),
            "visual_thickness_cm": round(support_panel_visual_thickness_cm, 4),
            "plywood_thickness_cm": 0.8,
            "carpet_thickness_cm": 0.2,
            "thickness_defined": True,
            "visual_thickness_only": False,
            "corners": support_panel_corners,
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
        "side_panels": side_panels,
        "folding": {"state": product_state, "folded_geometry_defined": False},
        # Temporary alias for clients created before the terminology correction.
        "side_rails": side_panels,
    }


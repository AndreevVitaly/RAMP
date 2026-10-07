from dataclasses import asdict, dataclass
from math import asin, degrees, sqrt

from .geometry import STEP_WIDTH_CM, RampGeometryError, build_side_profile
from .geometry_3d import build_ramp_geometry_3d

DEFAULT_WIDTH_CM = 40.0
DEFAULT_COLOR = "dark_gray"
ALLOWED_COLORS = ("dark_gray", "light_gray", "black", "beige")
FIRST_STEP_CM = 5.0
STEP_INTERVAL_CM = 14.0


@dataclass(frozen=True)
class RampConfiguration:
    height_cm: float
    width_cm: float
    ramp_length_cm: float
    recommended_length_cm: float
    uses_recommended_length: bool
    angle_deg: float
    horizontal_run_cm: float
    step_count: int
    step_width_cm: float
    step_positions_cm: list[float]
    geometry: dict
    geometry_3d: dict
    color: str
    side_rails: bool

    def to_dict(self):
        return asdict(self)


def calculate_step_positions(ramp_length_cm: float) -> list[float]:
    """Возвращает координаты реек вдоль наклонной поверхности."""
    positions = []
    position = FIRST_STEP_CM
    while position + STEP_WIDTH_CM <= ramp_length_cm:
        positions.append(position)
        position += STEP_INTERVAL_CM
    return positions


def calculate_ramp_configuration(
    *,
    height_cm: float,
    ramp_length_cm: float | None = None,
    width_cm: float = DEFAULT_WIDTH_CM,
    color: str = DEFAULT_COLOR,
    side_rails: bool = False,
) -> dict:
    height = float(height_cm)
    width = float(width_cm)
    recommended_length = height * 2
    uses_recommended = ramp_length_cm is None
    length = recommended_length if uses_recommended else float(ramp_length_cm)

    if width <= 0:
        raise RampGeometryError("Ширина должна быть больше 0 см.")
    if color not in ALLOWED_COLORS:
        raise RampGeometryError("Недопустимый цвет покрытия.")

    positions = calculate_step_positions(length)
    geometry = build_side_profile(
        height_cm=height,
        ramp_length_cm=length,
        step_positions_cm=positions,
    )
    horizontal_run = sqrt(length**2 - height**2)
    geometry_3d = build_ramp_geometry_3d(
        height_cm=height,
        ramp_length_cm=length,
        width_cm=width,
        angle_deg=round(degrees(asin(height / length)), 2),
        horizontal_run_cm=horizontal_run,
        base_length_cm=geometry["base_length_cm"],
        step_points=geometry["step_points"],
        support_hinge=geometry["points"]["support_hinge"],
        support_foot=geometry["points"]["support_foot"],
        side_rails_enabled=bool(side_rails),
    )
    result = RampConfiguration(
        height_cm=height,
        width_cm=width,
        ramp_length_cm=length,
        recommended_length_cm=recommended_length,
        uses_recommended_length=uses_recommended,
        angle_deg=round(degrees(asin(height / length)), 2),
        horizontal_run_cm=round(horizontal_run, 4),
        step_count=len(positions),
        step_width_cm=STEP_WIDTH_CM,
        step_positions_cm=positions,
        geometry=geometry,
        geometry_3d=geometry_3d,
        color=color,
        side_rails=bool(side_rails),
    )
    return result.to_dict()


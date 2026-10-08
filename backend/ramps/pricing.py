from dataclasses import asdict, dataclass
from decimal import Decimal

from .geometry import RampGeometryError


MIN_PRICED_LENGTH_CM = Decimal("60")
BASE_PRICE_RUB = Decimal("1600")
PRICE_PER_EXTRA_CM_RUB = Decimal("10")
SIDE_RAILS_PRICE_RUB = Decimal("500")
SLATS_PRICE_RUB = Decimal("0")


@dataclass(frozen=True)
class RampPrice:
    length_cm: float
    base_price_rub: float
    side_rails_price_rub: float
    slats_price_rub: float
    total_price_rub: float

    def to_dict(self):
        return asdict(self)


def calculate_ramp_price(*, length_cm: float, has_side_rails: bool, has_slats: bool = True) -> dict:
    """Calculate a transparent price breakdown independently from geometry."""
    length = Decimal(str(length_cm))
    if length < MIN_PRICED_LENGTH_CM:
        raise RampGeometryError("Минимальная длина пандуса для расчёта стоимости — 60 см.")

    base_price = BASE_PRICE_RUB + (length - MIN_PRICED_LENGTH_CM) * PRICE_PER_EXTRA_CM_RUB
    side_rails_price = SIDE_RAILS_PRICE_RUB if has_side_rails else Decimal("0")
    total = base_price + side_rails_price + SLATS_PRICE_RUB

    def number(value):
        value = value.quantize(Decimal("0.01"))
        return int(value) if value == value.to_integral() else float(value)

    return RampPrice(
        length_cm=number(length),
        base_price_rub=number(base_price),
        side_rails_price_rub=number(side_rails_price),
        slats_price_rub=number(SLATS_PRICE_RUB),
        total_price_rub=number(total),
    ).to_dict()

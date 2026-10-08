from django.test import SimpleTestCase

from ramps.geometry import RampGeometryError
from ramps.pricing import calculate_ramp_price
from ramps.services import calculate_ramp_configuration


class RampPricingTests(SimpleTestCase):
    def test_established_price_examples(self):
        examples = ((60, False, 1600), (100, False, 2000), (100, True, 2500), (150, True, 3000), (95, False, 1950))
        for length, rails, expected in examples:
            with self.subTest(length=length, rails=rails):
                price = calculate_ramp_price(length_cm=length, has_side_rails=rails)
                self.assertEqual(price["total_price_rub"], expected)

    def test_slats_are_free(self):
        with_slats = calculate_ramp_price(length_cm=100, has_side_rails=False, has_slats=True)
        without_slats = calculate_ramp_price(length_cm=100, has_side_rails=False, has_slats=False)
        self.assertEqual(with_slats, without_slats)
        self.assertEqual(with_slats["slats_price_rub"], 0)

    def test_length_below_sixty_is_rejected(self):
        with self.assertRaisesRegex(RampGeometryError, "60 см"):
            calculate_ramp_price(length_cm=59.9, has_side_rails=False)

    def test_non_pricing_configuration_does_not_change_price(self):
        baseline = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, support_panel_width_cm=20, color="dark_gray", has_slats=True)
        variants = (
            calculate_ramp_configuration(height_cm=40, ramp_length_cm=100, width_cm=40, support_panel_width_cm=20, color="dark_gray", has_slats=True),
            calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=55, support_panel_width_cm=20, color="dark_gray", has_slats=True),
            calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, support_panel_width_cm=18, color="dark_gray", has_slats=True),
            calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, support_panel_width_cm=20, color="beige", has_slats=True),
            calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, support_panel_width_cm=20, color="dark_gray", has_slats=False),
        )
        for variant in variants:
            self.assertEqual(variant["price"], baseline["price"])


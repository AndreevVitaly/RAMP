from django.test import SimpleTestCase

from ramps.services import RampGeometryError, calculate_ramp_configuration, calculate_step_positions


class RampCalculationTests(SimpleTestCase):
    def test_uses_recommended_length_by_default(self):
        result = calculate_ramp_configuration(height_cm=50)
        self.assertEqual(result["recommended_length_cm"], 100)
        self.assertEqual(result["ramp_length_cm"], 100)
        self.assertTrue(result["uses_recommended_length"])
        self.assertAlmostEqual(result["angle_deg"], 30)
        self.assertEqual(result["width_cm"], 40)
        self.assertFalse(result["side_rails"])

    def test_accepts_custom_length(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=120)
        self.assertEqual(result["recommended_length_cm"], 100)
        self.assertEqual(result["ramp_length_cm"], 120)
        self.assertFalse(result["uses_recommended_length"])
        self.assertLess(result["angle_deg"], 30)

    def test_step_positions_for_100_cm(self):
        self.assertEqual(calculate_step_positions(100), [5, 19, 33, 47, 61, 75, 89])

    def test_all_colors_are_accepted(self):
        for color in ("dark_gray", "light_gray", "black", "beige"):
            with self.subTest(color=color):
                self.assertEqual(calculate_ramp_configuration(height_cm=50, color=color)["color"], color)

    def test_rejects_invalid_geometry(self):
        invalid = ({"height_cm": 0}, {"height_cm": 50, "ramp_length_cm": 0}, {"height_cm": 50, "ramp_length_cm": 49})
        for params in invalid:
            with self.subTest(params=params), self.assertRaises(RampGeometryError):
                calculate_ramp_configuration(**params)


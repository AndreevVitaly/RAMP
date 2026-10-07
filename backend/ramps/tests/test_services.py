from django.test import SimpleTestCase

from math import cos, hypot, radians, sin

from ramps.geometry import BASE_VERTICAL_OFFSET_CM, SUPPORT_BASE_ANGLE_DEG
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
        invalid = ({"height_cm": 0}, {"height_cm": 50, "ramp_length_cm": 0}, {"height_cm": 50, "ramp_length_cm": 50}, {"height_cm": 50, "ramp_length_cm": 49})
        for params in invalid:
            with self.subTest(params=params), self.assertRaises(RampGeometryError):
                calculate_ramp_configuration(**params)

    def test_real_geometry_for_50_by_100(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)
        geometry = result["geometry"]
        points = geometry["points"]
        self.assertAlmostEqual(result["horizontal_run_cm"], 86.60, places=2)
        self.assertAlmostEqual(geometry["base_length_cm"], 81.6025, places=4)
        self.assertEqual(points["ramp_start"], {"x": 0.0, "y": 0.0})
        self.assertAlmostEqual(points["ramp_end"]["x"], 86.6025, places=4)
        self.assertEqual(points["ramp_end"]["y"], 50.0)
        self.assertAlmostEqual(points["vertical_projection"]["x"], 86.6025, places=4)
        self.assertEqual(points["vertical_projection"]["y"], 0.0)
        self.assertAlmostEqual(points["base_end"]["x"], 81.6025, places=4)
        self.assertEqual(points["base_end"]["y"], 0.0)
        self.assertEqual(geometry["base_vertical_offset_cm"], BASE_VERTICAL_OFFSET_CM)

    def test_support_intersects_ramp_at_105_degrees(self):
        geometry = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)["geometry"]
        c = geometry["points"]["base_end"]
        d = geometry["points"]["support_ramp_intersection"]
        b = geometry["points"]["ramp_end"]
        support_length = hypot(d["x"] - c["x"], d["y"] - c["y"])
        self.assertAlmostEqual(d["y"], (b["y"] / b["x"]) * d["x"], places=3)
        self.assertAlmostEqual(d["x"], c["x"] + support_length * cos(radians(SUPPORT_BASE_ANGLE_DEG)), places=3)
        self.assertAlmostEqual(d["y"], support_length * sin(radians(SUPPORT_BASE_ANGLE_DEG)), places=3)
        self.assertAlmostEqual(geometry["support_base_angle_deg"], 105)

    def test_geometry_for_60_by_120(self):
        result = calculate_ramp_configuration(height_cm=60, ramp_length_cm=120)
        self.assertAlmostEqual(result["angle_deg"], 30, places=2)
        self.assertAlmostEqual(result["horizontal_run_cm"], 103.92, places=2)
        self.assertAlmostEqual(result["geometry"]["base_length_cm"], 98.923, places=3)

    def test_custom_length_recalculates_entire_profile(self):
        standard = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)
        custom = calculate_ramp_configuration(height_cm=50, ramp_length_cm=120)
        self.assertLess(custom["angle_deg"], standard["angle_deg"])
        self.assertGreater(custom["horizontal_run_cm"], standard["horizontal_run_cm"])
        self.assertGreater(custom["geometry"]["base_length_cm"], standard["geometry"]["base_length_cm"])
        self.assertNotEqual(custom["geometry"]["support_length_cm"], standard["geometry"]["support_length_cm"])
        self.assertNotEqual(custom["geometry"]["step_points"], standard["geometry"]["step_points"])

    def test_step_points_lie_on_ramp_at_requested_distance(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=120)
        ramp_end = result["geometry"]["points"]["ramp_end"]
        for point in result["geometry"]["step_points"]:
            with self.subTest(point=point):
                self.assertAlmostEqual(point["y"], (ramp_end["y"] / ramp_end["x"]) * point["x"], places=3)
                self.assertAlmostEqual(hypot(point["x"], point["y"]), point["distance_cm"], places=3)


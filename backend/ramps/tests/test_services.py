from django.test import SimpleTestCase

from math import cos, hypot, radians, sin

from ramps.geometry import (
    BASE_VERTICAL_OFFSET_CM,
    SUPPORT_BASE_ANGLE_DEG,
    SUPPORT_DEPLOYED_STATE,
    SUPPORT_FOLD_DIRECTION,
    SUPPORT_FLOOR_ANGLE_DEG,
    SUPPORT_HINGE_COUNT,
    SUPPORT_HINGE_POSITION_RATIO,
)
from ramps.services import STEP_WIDTH_CM, RampGeometryError, calculate_ramp_configuration, calculate_step_positions


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

    def test_step_intervals_for_100_cm(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)
        intervals = [(step["start_distance_cm"], step["end_distance_cm"]) for step in result["geometry"]["step_points"]]
        self.assertEqual(intervals, [(5, 8), (19, 22), (33, 36), (47, 50), (61, 64), (75, 78), (89, 92)])
        self.assertEqual(result["step_width_cm"], STEP_WIDTH_CM)
        for previous, current in zip(result["geometry"]["step_points"], result["geometry"]["step_points"][1:]):
            self.assertEqual(current["start_distance_cm"] - previous["start_distance_cm"], 14)
            self.assertEqual(current["start_distance_cm"] - previous["end_distance_cm"], 11)

    def test_steps_fit_for_supported_lengths(self):
        expected_counts = {80: 6, 100: 7, 120: 9, 140: 10}
        for length, count in expected_counts.items():
            with self.subTest(length=length):
                result = calculate_ramp_configuration(height_cm=40, ramp_length_cm=length)
                self.assertEqual(result["step_count"], count)
                self.assertTrue(all(step["end_distance_cm"] <= length for step in result["geometry"]["step_points"]))

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

    def test_support_hinge_is_on_ramp_and_foot_is_inside_base(self):
        geometry = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)["geometry"]
        a = geometry["points"]["ramp_start"]
        c = geometry["points"]["base_end"]
        d = geometry["points"]["support_hinge"]
        s = geometry["points"]["support_foot"]
        b = geometry["points"]["ramp_end"]
        self.assertAlmostEqual(d["y"], (b["y"] / b["x"]) * d["x"], places=3)
        self.assertGreater(s["x"], a["x"])
        self.assertLess(s["x"], c["x"])
        self.assertLess(s["x"], d["x"])
        self.assertEqual(s["y"], 0.0)
        self.assertEqual(geometry["support_floor_angle_deg"], 105)

    def test_support_hinge_is_at_75_percent_for_50_by_100(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)
        geometry = result["geometry"]
        d = geometry["points"]["support_hinge"]
        self.assertAlmostEqual(d["x"], 64.9519, places=4)
        self.assertEqual(d["y"], 37.5)
        self.assertEqual(geometry["support"]["hinge_position_ratio"], SUPPORT_HINGE_POSITION_RATIO)
        self.assertEqual(geometry["support"]["hinge_distance_cm"], 75.0)
        self.assertEqual(geometry["measurements"]["ramp_start_to_hinge_cm"], 75.0)
        self.assertEqual(geometry["support_length_cm"], geometry["support"]["length_cm"])
        self.assertEqual(geometry["support_length_cm"], geometry["measurements"]["support_length_cm"])

    def test_support_geometry_scales_for_similar_ramps(self):
        normalized = []
        foot_ratios = []
        for height, length in ((50, 100), (60, 120), (70, 140)):
            result = calculate_ramp_configuration(height_cm=height, ramp_length_cm=length)
            geometry = result["geometry"]
            d = geometry["points"]["support_hinge"]
            s = geometry["points"]["support_foot"]
            normalized.append((d["x"] / result["horizontal_run_cm"], d["y"] / height))
            foot_ratios.append(s["x"] / height)
        for x_ratio, y_ratio in normalized:
            self.assertAlmostEqual(x_ratio, 0.75, places=3)
            self.assertAlmostEqual(y_ratio, 0.75, places=3)
        self.assertAlmostEqual(foot_ratios[0], foot_ratios[1], places=3)
        self.assertAlmostEqual(foot_ratios[1], foot_ratios[2], places=3)

    def test_custom_length_keeps_hinge_at_75_percent(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=120)
        geometry = result["geometry"]
        d = geometry["points"]["support_hinge"]
        self.assertAlmostEqual(d["x"] / result["horizontal_run_cm"], 0.75, places=3)
        self.assertAlmostEqual(d["y"] / result["height_cm"], 0.75, places=3)
        self.assertEqual(geometry["support"]["hinge_distance_cm"], 90.0)
        self.assertEqual(geometry["support_stop"]["contact_point"], geometry["points"]["support_foot"])

    def test_support_direction_matches_105_degree_floor_angle(self):
        geometry = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)["geometry"]
        d = geometry["points"]["support_hinge"]
        s = geometry["points"]["support_foot"]
        support_length = hypot(d["x"] - s["x"], d["y"] - s["y"])
        direction = 180 - SUPPORT_FLOOR_ANGLE_DEG
        self.assertAlmostEqual(d["x"], s["x"] + support_length * cos(radians(direction)), places=3)
        self.assertAlmostEqual(d["y"], s["y"] + support_length * sin(radians(direction)), places=3)
        self.assertGreater(d["x"], s["x"])
        self.assertGreater(d["y"], s["y"])

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
        # With the same height, D.y = 0.75 * height and a fixed support angle,
        # so the support length stays equal while its X position changes.
        self.assertEqual(custom["geometry"]["support_length_cm"], standard["geometry"]["support_length_cm"])
        self.assertNotEqual(custom["geometry"]["points"]["support_foot"], standard["geometry"]["points"]["support_foot"])
        self.assertNotEqual(custom["geometry"]["step_points"], standard["geometry"]["step_points"])

    def test_step_points_lie_on_ramp_at_requested_distance(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=120)
        ramp_end = result["geometry"]["points"]["ramp_end"]
        for point in result["geometry"]["step_points"]:
            with self.subTest(point=point):
                self.assertAlmostEqual(point["start"]["y"], (ramp_end["y"] / ramp_end["x"]) * point["start"]["x"], places=3)
                self.assertAlmostEqual(hypot(point["start"]["x"], point["start"]["y"]), point["start_distance_cm"], places=3)
                self.assertAlmostEqual(hypot(point["end"]["x"], point["end"]["y"]), point["end_distance_cm"], places=3)

    def test_support_is_a_folding_hinged_component(self):
        geometry = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)["geometry"]
        support = geometry["support"]
        hinge = geometry["support_hinge"]
        self.assertEqual(support["type"], "folding")
        self.assertEqual(support["state"], SUPPORT_DEPLOYED_STATE)
        self.assertTrue(support["hinged"])
        self.assertEqual(support["fold_direction"], SUPPORT_FOLD_DIRECTION)
        self.assertEqual(support["base_angle_deg"], SUPPORT_BASE_ANGLE_DEG)
        self.assertEqual(hinge["hinge_count"], SUPPORT_HINGE_COUNT)
        self.assertEqual(hinge["point"], geometry["points"]["support_hinge"])

    def test_support_lower_end_is_free_and_rests_on_stop(self):
        geometry = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100)["geometry"]
        lower_connection = geometry["support"]["lower_connection"]
        stop = geometry["support_stop"]
        self.assertEqual(lower_connection["type"], "free_contact")
        self.assertFalse(lower_connection["hinged"])
        self.assertEqual(lower_connection["rests_on"], "support_stop")
        self.assertEqual(stop["type"], "mechanical_stop")
        self.assertFalse(stop["dimensions_defined"])
        self.assertEqual(stop["contact_point"], geometry["points"]["support_foot"])
        self.assertNotEqual(stop["contact_point"], geometry["points"]["base_end"])
        self.assertEqual(lower_connection["point"], stop["contact_point"])


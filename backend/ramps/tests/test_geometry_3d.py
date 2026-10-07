from math import dist

from django.test import SimpleTestCase

from ramps.services import calculate_ramp_configuration
from ramps.geometry_3d import SIDE_RAIL_HEIGHT_CM


class RampGeometry3DTests(SimpleTestCase):
    def test_surface_and_base_corners_for_standard_ramp(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)
        model = result["geometry_3d"]
        surface = model["ramp_surface"]["corners"]
        self.assertEqual(surface["a_left"], {"x": 0, "y": 0, "z": 0})
        self.assertEqual(surface["a_right"], {"x": 0, "y": 40, "z": 0})
        self.assertEqual(surface["b_left"], {"x": 86.6025, "y": 0, "z": 50})
        self.assertEqual(surface["b_right"], {"x": 86.6025, "y": 40, "z": 50})
        self.assertEqual(dist(surface["a_left"].values(), surface["a_right"].values()), 40)
        for corner in model["base"]["corners"].values():
            self.assertEqual(corner["z"], 0)

    def test_steps_cross_entire_width(self):
        model = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)["geometry_3d"]
        for step in model["steps"]:
            with self.subTest(step=step):
                self.assertEqual(step["start_left"]["x"], step["start_right"]["x"])
                self.assertEqual(step["start_left"]["z"], step["start_right"]["z"])
                self.assertEqual(step["start_right"]["y"] - step["start_left"]["y"], 40)
                self.assertEqual(step["end_right"]["y"] - step["end_left"]["y"], 40)
                self.assertEqual(step["end_distance_cm"] - step["start_distance_cm"], 3)

    def test_custom_width_only_changes_y_extent(self):
        standard = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)["geometry_3d"]
        custom = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=55)["geometry_3d"]
        for name in standard["ramp_surface"]["corners"]:
            p40 = standard["ramp_surface"]["corners"][name]
            p55 = custom["ramp_surface"]["corners"][name]
            self.assertEqual((p40["x"], p40["z"]), (p55["x"], p55["z"]))
        self.assertEqual(custom["ramp_surface"]["corners"]["b_right"]["y"], 55)
        self.assertEqual(custom["steps"][0]["start_right"]["y"], 55)
        self.assertEqual(custom["support"]["center_y_cm"], 27.5)

    def test_projections_can_share_the_same_b_point(self):
        model = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)["geometry_3d"]
        b = model["ramp_surface"]["corners"]["b_right"]
        self.assertEqual((b["x"], b["z"]), (86.6025, 50))  # side XZ
        self.assertEqual((b["x"], b["y"]), (86.6025, 40))  # top XY
        self.assertEqual((b["y"], b["z"]), (40, 50))  # front YZ

    def test_enabled_side_rails_have_normal_height_and_area(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, side_rails=True)
        rails = result["geometry_3d"]["side_rails"]
        self.assertTrue(rails["enabled"])
        self.assertEqual(rails["count"], 2)
        self.assertEqual(rails["length_cm"], 100)
        self.assertEqual(rails["height_cm"], SIDE_RAIL_HEIGHT_CM)
        self.assertEqual(rails["area_each_cm2"], 500)
        self.assertEqual(rails["area_total_cm2"], 1000)
        for name in ("left", "right"):
            rail = rails[name]
            normal_distance = dist(
                (rail["bottom_start"]["x"], rail["bottom_start"]["z"]),
                (rail["top_start"]["x"], rail["top_start"]["z"]),
            )
            rail_length = dist(
                (rail["bottom_start"]["x"], rail["bottom_start"]["z"]),
                (rail["bottom_end"]["x"], rail["bottom_end"]["z"]),
            )
            self.assertAlmostEqual(normal_distance, 5, places=4)
            self.assertAlmostEqual(rail_length, 100, places=4)
        self.assertEqual(rails["left"]["bottom_start"]["y"], 0)
        self.assertEqual(rails["right"]["bottom_start"]["y"], 40)

    def test_disabled_side_rails_have_no_geometry(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, side_rails=False)
        rails = result["geometry_3d"]["side_rails"]
        self.assertEqual(rails, {"enabled": False, "count": 0})

    def test_side_rails_follow_length_and_width(self):
        for height, length, width in ((50, 100, 40), (60, 120, 40), (70, 140, 40), (50, 100, 55)):
            with self.subTest(height=height, length=length, width=width):
                rails = calculate_ramp_configuration(height_cm=height, ramp_length_cm=length, width_cm=width, side_rails=True)["geometry_3d"]["side_rails"]
                self.assertEqual(rails["length_cm"], length)
                self.assertEqual(rails["height_cm"], 5)
                self.assertEqual(rails["left"]["bottom_start"]["y"], 0)
                self.assertEqual(rails["right"]["bottom_start"]["y"], width)

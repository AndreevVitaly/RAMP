from math import dist

from django.test import SimpleTestCase

from ramps.services import calculate_ramp_configuration


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
                self.assertEqual(step["left"]["x"], step["right"]["x"])
                self.assertEqual(step["left"]["z"], step["right"]["z"])
                self.assertEqual(step["right"]["y"] - step["left"]["y"], 40)

    def test_custom_width_only_changes_y_extent(self):
        standard = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)["geometry_3d"]
        custom = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=55)["geometry_3d"]
        for name in standard["ramp_surface"]["corners"]:
            p40 = standard["ramp_surface"]["corners"][name]
            p55 = custom["ramp_surface"]["corners"][name]
            self.assertEqual((p40["x"], p40["z"]), (p55["x"], p55["z"]))
        self.assertEqual(custom["ramp_surface"]["corners"]["b_right"]["y"], 55)
        self.assertEqual(custom["steps"][0]["right"]["y"], 55)
        self.assertEqual(custom["support"]["center_y_cm"], 27.5)

    def test_projections_can_share_the_same_b_point(self):
        model = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)["geometry_3d"]
        b = model["ramp_surface"]["corners"]["b_right"]
        self.assertEqual((b["x"], b["z"]), (86.6025, 50))  # side XZ
        self.assertEqual((b["x"], b["y"]), (86.6025, 40))  # top XY
        self.assertEqual((b["y"], b["z"]), (40, 50))  # front YZ

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
                self.assertEqual(step["start_left"]["x"], step["start_right"]["x"])
                self.assertEqual(step["start_left"]["z"], step["start_right"]["z"])
                self.assertEqual(step["start_right"]["y"] - step["start_left"]["y"], 40)
                self.assertEqual(step["end_right"]["y"] - step["end_left"]["y"], 40)
                self.assertEqual(step["end_distance_cm"] - step["start_distance_cm"], 3)

    def test_disabled_slats_are_absent_from_unified_3d_model(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, has_slats=False)
        self.assertEqual(result["geometry_3d"]["steps"], [])
        self.assertEqual(result["geometry"]["step_points"], [])

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

    def test_support_panel_is_centered_and_twenty_centimeters_wide(self):
        model = calculate_ramp_configuration(
            height_cm=50,
            ramp_length_cm=100,
            width_cm=40,
            support_panel_width_cm=20,
        )["geometry_3d"]
        support = model["support"]
        corners = support["corners"]
        self.assertEqual(support["panel_width_cm"], 20)
        self.assertEqual(support["center_y_cm"], 20)
        self.assertEqual((support["y_min_cm"], support["y_max_cm"]), (10, 30))
        self.assertEqual(support["thickness_cm"], 1)
        self.assertTrue(support["thickness_defined"])
        self.assertFalse(support["visual_thickness_only"])
        for endpoint in ("foot", "hinge"):
            for face in ("front", "back"):
                left = corners[f"{endpoint}_left_{face}"]
                right = corners[f"{endpoint}_right_{face}"]
                self.assertEqual(right["y"] - left["y"], 20)
                self.assertEqual((left["x"], left["z"]), (right["x"], right["z"]))

    def test_support_panel_axis_matches_side_profile_points(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)
        support = result["geometry_3d"]["support"]
        side_points = result["geometry"]["points"]
        self.assertEqual(support["axis"]["foot"], {"x": side_points["support_foot"]["x"], "y": 20, "z": side_points["support_foot"]["y"]})
        self.assertEqual(support["axis"]["hinge"], {"x": side_points["support_hinge"]["x"], "y": 20, "z": side_points["support_hinge"]["y"]})
        self.assertEqual(support["length_cm"], result["geometry"]["support_length_cm"])

    def test_projections_can_share_the_same_b_point(self):
        model = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)["geometry_3d"]
        b = model["ramp_surface"]["corners"]["b_right"]
        self.assertEqual((b["x"], b["z"]), (86.6025, 50))  # side XZ
        self.assertEqual((b["x"], b["y"]), (86.6025, 40))  # top XY
        self.assertEqual((b["y"], b["z"]), (40, 50))  # front YZ

    def test_finished_panel_volumes_use_eight_mm_plywood_and_two_mm_carpet(self):
        model = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40)["geometry_3d"]
        self.assertEqual(model["ramp_surface"]["finished_thickness_cm"], 1)
        self.assertEqual(model["ramp_surface"]["plywood_thickness_cm"], 0.8)
        self.assertEqual(model["ramp_surface"]["carpet_thickness_cm"], 0.2)
        self.assertEqual(len(model["ramp_surface"]["volume_corners"]), 8)
        self.assertEqual(model["base"]["finished_thickness_cm"], 1)
        self.assertEqual(len(model["base"]["volume_corners"]), 8)

    def test_folded_state_is_recorded_without_invented_geometry(self):
        result = calculate_ramp_configuration(height_cm=50, product_state="folded")
        self.assertEqual(result["product_state"], "folded")
        self.assertEqual(result["geometry_3d"]["folding"], {"state": "folded", "folded_geometry_defined": False})

    def test_enabled_side_panels_have_real_height_and_area(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, side_rails=True)
        panels = result["geometry_3d"]["side_panels"]
        self.assertTrue(panels["enabled"])
        self.assertEqual(panels["count"], 2)
        self.assertEqual(panels["length_cm"], 100)
        self.assertEqual(panels["height_cm"], 5)
        self.assertEqual(panels["area_each_one_side_cm2"], 500)
        self.assertEqual(panels["area_total_one_side_cm2"], 1000)
        self.assertFalse(panels["thickness_defined"])
        for name in ("left", "right"):
            panel = panels[name]
            panel_length = dist(panel["top_start"].values(), panel["top_end"].values())
            self.assertAlmostEqual(panel_length, 100, places=4)
            self.assertAlmostEqual(dist(panel["top_start"].values(), panel["bottom_start"].values()), 5, places=4)
            self.assertAlmostEqual(dist(panel["top_end"].values(), panel["bottom_end"].values()), 5, places=4)
            self.assertGreater(panel["top_start"]["z"], panel["bottom_start"]["z"])
            self.assertLess(panel["top_start"]["x"], panel["bottom_start"]["x"])
        self.assertEqual(panels["left"]["bottom_start"], {"x": 0, "y": 0, "z": 0})
        self.assertEqual(panels["left"]["bottom_end"], {"x": 86.6025, "y": 0, "z": 50})
        self.assertEqual(panels["right"]["bottom_start"], {"x": 0, "y": 40, "z": 0})
        self.assertEqual(panels["right"]["bottom_end"], {"x": 86.6025, "y": 40, "z": 50})
        self.assertEqual(result["geometry_3d"]["side_rails"], panels)
        self.assertEqual(len(result["geometry_3d"]["steps"]), 7)

    def test_disabled_side_rails_have_no_geometry(self):
        result = calculate_ramp_configuration(height_cm=50, ramp_length_cm=100, width_cm=40, side_rails=False)
        panels = result["geometry_3d"]["side_panels"]
        self.assertEqual(panels, {"enabled": False, "count": 0})
        self.assertEqual(result["geometry_3d"]["side_rails"], panels)

    def test_side_panels_follow_length_width_and_surface_normal(self):
        for height, length, width in ((50, 80, 40), (50, 100, 40), (50, 120, 40), (50, 140, 40), (50, 100, 55)):
            with self.subTest(height=height, length=length, width=width):
                panels = calculate_ramp_configuration(height_cm=height, ramp_length_cm=length, width_cm=width, side_rails=True)["geometry_3d"]["side_panels"]
                self.assertEqual(panels["length_cm"], length)
                self.assertEqual(panels["height_cm"], 5)
                self.assertEqual(panels["area_each_one_side_cm2"], length * 5)
                self.assertEqual(panels["area_total_one_side_cm2"], length * 10)
                self.assertEqual(panels["left"]["bottom_start"]["y"], 0)
                self.assertEqual(panels["right"]["bottom_start"]["y"], width)
                for name in ("left", "right"):
                    panel = panels[name]
                    along = tuple(panel["bottom_end"][axis] - panel["bottom_start"][axis] for axis in ("x", "y", "z"))
                    upward = tuple(panel["top_start"][axis] - panel["bottom_start"][axis] for axis in ("x", "y", "z"))
                    relative_dot = abs(sum(a * b for a, b in zip(along, upward))) / (length * 5)
                    self.assertLess(relative_dot, 0.0002)
                    self.assertAlmostEqual(dist(panel["top_start"].values(), panel["bottom_start"].values()), 5, places=4)
                    self.assertGreater(panel["top_start"]["z"], panel["bottom_start"]["z"])

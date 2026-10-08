from rest_framework import status
from rest_framework.test import APITestCase


class RampCalculationApiTests(APITestCase):
    url = "/api/ramp/calculate/"

    def test_calculates_preview_with_defaults(self):
        response = self.client.post(self.url, {"height_cm": 50, "color": "beige"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ramp_length_cm"], 100)
        self.assertEqual(response.data["step_count"], 7)
        self.assertTrue(response.data["has_slats"])
        self.assertEqual(response.data["slat_total_length_cm"], 280)
        self.assertEqual(response.data["product_state"], "deployed")
        self.assertEqual(response.data["geometry_3d"]["ramp_surface"]["finished_thickness_cm"], 1)
        self.assertEqual(response.data["price"]["total_price_rub"], 2000)
        self.assertIn("geometry", response.data)
        self.assertEqual(len(response.data["geometry"]["step_points"]), 7)
        self.assertEqual(response.data["geometry"]["support"]["type"], "folding")
        self.assertEqual(response.data["geometry"]["support_hinge"]["hinge_count"], 2)
        self.assertEqual(response.data["geometry"]["support"]["hinge_position_ratio"], 0.75)
        self.assertEqual(response.data["geometry"]["support"]["hinge_distance_cm"], 75.0)
        self.assertEqual(
            response.data["geometry"]["support_stop"]["contact_point"],
            response.data["geometry"]["points"]["support_foot"],
        )
        self.assertNotEqual(
            response.data["geometry"]["points"]["support_foot"],
            response.data["geometry"]["points"]["base_end"],
        )

    def test_calculates_preview_with_custom_values(self):
        response = self.client.post(self.url, {"height_cm": 50, "ramp_length_cm": 120, "width_cm": 55, "support_panel_width_cm": 20, "side_rails": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["width_cm"], 55)
        self.assertTrue(response.data["side_rails"])
        self.assertTrue(response.data["geometry_3d"]["side_panels"]["enabled"])
        self.assertEqual(response.data["geometry_3d"]["side_panels"]["count"], 2)
        self.assertEqual(response.data["geometry_3d"]["side_panels"]["height_cm"], 5)
        self.assertEqual(response.data["geometry_3d"]["side_panels"]["area_each_one_side_cm2"], 600)
        self.assertEqual(response.data["geometry_3d"]["side_panels"]["area_total_one_side_cm2"], 1200)
        self.assertFalse(response.data["geometry_3d"]["side_panels"]["thickness_defined"])
        self.assertEqual(response.data["geometry_3d"]["support"]["panel_width_cm"], 20)
        self.assertEqual(response.data["geometry_3d"]["support"]["y_min_cm"], 17.5)
        self.assertEqual(response.data["geometry_3d"]["support"]["y_max_cm"], 37.5)

    def test_rejects_invalid_input(self):
        for payload in ({"height_cm": 0}, {"height_cm": 50, "ramp_length_cm": -1}, {"height_cm": 50, "ramp_length_cm": 50}, {"height_cm": 50, "ramp_length_cm": 40}, {"height_cm": 50, "color": "red"}, {"height_cm": 50, "width_cm": 40, "support_panel_width_cm": 41}, {"height_cm": 50, "product_state": "broken"}):
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_all_slat_and_side_panel_combinations_are_independent(self):
        for has_slats in (True, False):
            for side_rails in (True, False):
                with self.subTest(has_slats=has_slats, side_rails=side_rails):
                    response = self.client.post(
                        self.url,
                        {"height_cm": 50, "ramp_length_cm": 100, "width_cm": 40, "has_slats": has_slats, "side_rails": side_rails},
                        format="json",
                    )
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    self.assertEqual(response.data["has_slats"], has_slats)
                    self.assertEqual(response.data["side_rails"], side_rails)
                    self.assertEqual(response.data["geometry_3d"]["side_panels"]["enabled"], side_rails)
                    expected_count = 7 if has_slats else 0
                    self.assertEqual(response.data["step_count"], expected_count)
                    self.assertEqual(len(response.data["geometry_3d"]["steps"]), expected_count)
                    self.assertEqual(response.data["slat_total_length_cm"], expected_count * 40)

    def test_folded_state_is_saved_but_not_presented_as_verified_geometry(self):
        response = self.client.post(self.url, {"height_cm": 50, "product_state": "folded"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["product_state"], "folded")
        self.assertFalse(response.data["geometry_3d"]["folding"]["folded_geometry_defined"])

    def test_price_updates_with_length_and_side_panels(self):
        for length, side_rails, expected in ((60, False, 1600), (100, False, 2000), (100, True, 2500), (150, True, 3000)):
            with self.subTest(length=length, side_rails=side_rails):
                response = self.client.post(self.url, {"height_cm": 40, "ramp_length_cm": length, "side_rails": side_rails}, format="json")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["price"]["total_price_rub"], expected)


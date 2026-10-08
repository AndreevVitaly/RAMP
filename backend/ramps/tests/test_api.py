from rest_framework import status
from rest_framework.test import APITestCase


class RampCalculationApiTests(APITestCase):
    url = "/api/ramp/calculate/"

    def test_calculates_preview_with_defaults(self):
        response = self.client.post(self.url, {"height_cm": 50, "color": "beige"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ramp_length_cm"], 100)
        self.assertEqual(response.data["step_count"], 7)
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
        response = self.client.post(self.url, {"height_cm": 50, "ramp_length_cm": 120, "width_cm": 55, "side_rails": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["width_cm"], 55)
        self.assertTrue(response.data["side_rails"])
        self.assertTrue(response.data["geometry_3d"]["side_panels"]["enabled"])
        self.assertEqual(response.data["geometry_3d"]["side_panels"]["count"], 2)
        self.assertEqual(response.data["geometry_3d"]["side_panels"]["height_cm"], 5)
        self.assertEqual(response.data["geometry_3d"]["side_panels"]["area_each_one_side_cm2"], 600)
        self.assertEqual(response.data["geometry_3d"]["side_panels"]["area_total_one_side_cm2"], 1200)
        self.assertFalse(response.data["geometry_3d"]["side_panels"]["thickness_defined"])

    def test_rejects_invalid_input(self):
        for payload in ({"height_cm": 0}, {"height_cm": 50, "ramp_length_cm": -1}, {"height_cm": 50, "ramp_length_cm": 50}, {"height_cm": 50, "ramp_length_cm": 40}, {"height_cm": 50, "color": "red"}):
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


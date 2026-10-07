from rest_framework import status
from rest_framework.test import APITestCase


class RampCalculationApiTests(APITestCase):
    url = "/api/ramp/calculate/"

    def test_calculates_preview_with_defaults(self):
        response = self.client.post(self.url, {"height_cm": 50, "color": "beige"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ramp_length_cm"], 100)
        self.assertEqual(response.data["step_count"], 7)

    def test_calculates_preview_with_custom_values(self):
        response = self.client.post(self.url, {"height_cm": 50, "ramp_length_cm": 120, "width_cm": 55, "side_rails": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["width_cm"], 55)
        self.assertTrue(response.data["side_rails"])

    def test_rejects_invalid_input(self):
        for payload in ({"height_cm": 0}, {"height_cm": 50, "ramp_length_cm": -1}, {"height_cm": 50, "ramp_length_cm": 40}, {"height_cm": 50, "color": "red"}):
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


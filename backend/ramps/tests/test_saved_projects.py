from rest_framework.test import APITestCase

from ramps.accounts import issue_session
from ramps.models import Customer, SavedProject


class SavedProjectsTests(APITestCase):
    url = "/api/ramp/account/projects/"

    def setUp(self):
        self.customer = Customer.objects.create(name="Анна", email="anna@example.com", email_verified=True)
        self.other = Customer.objects.create(name="Борис", email="boris@example.com", email_verified=True)
        self.token = issue_session(self.customer)
        self.other_token = issue_session(self.other)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.configuration = {
            "height_cm": 50, "ramp_length_cm": 100, "width_cm": 40,
            "support_panel_width_cm": 20, "color": "beige",
            "has_slats": True, "side_rails": False, "product_state": "deployed",
            "pet": {"breed": "corgi", "enabled": True, "height_cm": 999},
        }

    def test_save_and_list_restorable_parameters(self):
        created = self.client.post(self.url, {"name": "Для дивана", "configuration": self.configuration}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["name"], "Для дивана")
        self.assertEqual(created.data["configuration"]["pet"], {"breed": "corgi", "enabled": True})
        self.assertEqual(created.data["configuration"]["ramp_length_cm"], 100)
        listed = self.client.get(self.url)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([project["id"] for project in listed.data], [created.data["id"]])

    def test_projects_are_private_to_each_customer(self):
        self.client.post(self.url, {"configuration": self.configuration}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_token}")
        self.assertEqual(self.client.get(self.url).data, [])
        self.assertEqual(SavedProject.objects.filter(customer=self.other).count(), 0)

    def test_owner_can_delete_project_but_other_customer_cannot(self):
        created = self.client.post(self.url, {"configuration": self.configuration}, format="json")
        detail_url = f"{self.url}{created.data['id']}/"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_token}")
        self.assertEqual(self.client.delete(detail_url).status_code, 404)
        self.assertEqual(SavedProject.objects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(self.client.delete(detail_url).status_code, 204)
        self.assertEqual(self.client.get(self.url).data, [])

    def test_guest_cannot_delete_project(self):
        created = self.client.post(self.url, {"configuration": self.configuration}, format="json")
        self.client.credentials()
        self.assertIn(self.client.delete(f"{self.url}{created.data['id']}/").status_code, (401, 403))
        self.assertEqual(SavedProject.objects.count(), 1)

    def test_guest_cannot_list_or_save(self):
        self.client.credentials()
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
        self.assertIn(self.client.post(self.url, {"configuration": self.configuration}, format="json").status_code, (401, 403))
        self.assertEqual(SavedProject.objects.count(), 0)

    def test_invalid_geometry_and_breed_are_not_saved(self):
        for changes in ({"ramp_length_cm": 40}, {"pet": {"breed": "unknown", "enabled": True}}):
            with self.subTest(changes=changes):
                response = self.client.post(self.url, {"configuration": {**self.configuration, **changes}}, format="json")
                self.assertEqual(response.status_code, 400)
        self.assertEqual(SavedProject.objects.count(), 0)

    def test_unnamed_project_gets_product_based_name(self):
        response = self.client.post(self.url, {"configuration": self.configuration}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("50", response.data["name"])
        self.assertIn("100", response.data["name"])

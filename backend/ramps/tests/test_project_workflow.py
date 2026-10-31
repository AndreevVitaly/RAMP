from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from ramps.accounts import issue_admin_token, issue_session
from ramps.models import Customer, SavedProject


class ProjectWorkflowTests(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Анна", email="anna@example.com", email_verified=True)
        self.other = Customer.objects.create(name="Борис", email="boris@example.com", email_verified=True)
        self.admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "test-password")
        self.first = SavedProject.objects.create(customer=self.customer, name="Первый", configuration={"height_cm": 50})
        self.second = SavedProject.objects.create(customer=self.customer, name="Второй", configuration={"height_cm": 40})

    def as_customer(self, customer=None):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_session(customer or self.customer)}")

    def as_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_admin_token(self.admin)}")

    def test_customer_submission_and_admin_alternative_are_visible_to_both(self):
        self.as_customer()
        response = self.client.post(f"/api/ramp/account/projects/{self.first.pk}/submit/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "submitted")
        self.assertEqual(self.client.get("/api/ramp/account/projects/").data[1]["status"], "submitted")

        self.as_admin()
        projects = self.client.get("/api/ramp/admin/projects/").data
        self.assertEqual(next(item for item in projects if item["id"] == self.first.pk)["status"], "submitted")
        planned = (timezone.localdate() + timedelta(days=10)).isoformat()
        accepted = self.client.post(f"/api/ramp/admin/projects/{self.second.pk}/status/", {"action": "accept", "planned_completion_date": planned}, format="json")
        self.assertEqual(accepted.status_code, 200)
        self.assertTrue(accepted.data["selected_by_admin"])
        self.assertEqual(accepted.data["planned_completion_date"], planned)
        self.first.refresh_from_db()
        self.assertEqual(self.first.status, "saved")

        self.as_customer()
        customer_project = next(item for item in self.client.get("/api/ramp/account/projects/").data if item["id"] == self.second.pk)
        self.assertEqual(customer_project["status"], "in_progress")
        self.assertEqual(customer_project["planned_completion_date"], planned)
        self.assertEqual(self.client.delete(f"/api/ramp/account/projects/{self.second.pk}/").status_code, 400)

        self.as_admin()
        completed = self.client.post(f"/api/ramp/admin/projects/{self.second.pk}/status/", {"action": "complete"}, format="json")
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.data["status"], "completed")
        self.as_customer()
        self.assertEqual(self.client.get("/api/ramp/account/projects/").data[0]["status"], "completed")

    def test_only_owner_submits_and_only_admin_changes_work_status(self):
        self.as_customer(self.other)
        self.assertEqual(self.client.post(f"/api/ramp/account/projects/{self.first.pk}/submit/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/ramp/admin/projects/{self.first.pk}/status/", {"action": "complete"}, format="json").status_code, 403)
        self.as_admin()
        self.assertEqual(self.client.post(f"/api/ramp/admin/projects/{self.first.pk}/status/", {"action": "complete"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(f"/api/ramp/admin/projects/{self.first.pk}/status/", {"action": "accept"}, format="json").status_code, 400)

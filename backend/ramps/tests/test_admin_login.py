from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from ramps.accounts import issue_session
from ramps.models import AdminContactSettings, Customer, SavedProject


class UnifiedAdminLoginTests(APITestCase):
    login_url = "/api/ramp/admin/login/"
    settings_url = "/api/ramp/admin/settings/"
    briefs_url = "/api/ramp/admin/briefs/"
    projects_url = "/api/ramp/admin/projects/"

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="temporary-test-password"
        )

    def login(self, password="temporary-test-password"):
        return self.client.post(
            self.login_url, {"username": "admin", "password": password}, format="json"
        )

    def test_django_superuser_credentials_open_ramp_admin(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['token']}")
        self.assertEqual(self.client.get(self.briefs_url).status_code, 200)
        self.assertEqual(
            self.client.put(self.settings_url, {"email": "admin@example.com"}, format="json").status_code,
            200,
        )
        self.assertEqual(AdminContactSettings.objects.first().email, "admin@example.com")

    def test_wrong_password_and_nonstaff_user_cannot_log_in(self):
        self.assertEqual(self.login("wrong-password").status_code, 403)
        self.user.is_staff = False
        self.user.save(update_fields=("is_staff",))
        self.assertEqual(self.login().status_code, 403)

    def test_legacy_key_no_longer_grants_access(self):
        self.client.credentials(HTTP_X_ADMIN_KEY="obsolete-key")
        self.assertEqual(self.client.get(self.briefs_url).status_code, 403)
        self.assertEqual(
            self.client.put(self.settings_url, {"email": "attacker@example.com"}, format="json").status_code,
            403,
        )

    def test_admin_sees_all_saved_projects_with_customer_and_customer_cannot(self):
        anna = Customer.objects.create(name="Анна", email="anna@example.com", email_verified=True)
        boris = Customer.objects.create(name="Борис", email="boris@example.com", email_verified=True)
        parameters = {"height_cm": 50, "ramp_length_cm": 100, "width_cm": 40, "color": "beige"}
        SavedProject.objects.create(customer=anna, name="Для дивана", configuration=parameters)
        SavedProject.objects.create(customer=boris, name="Для кровати", configuration={**parameters, "height_cm": 40})

        self.assertEqual(self.client.get(self.projects_url).status_code, 403)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_session(anna)}")
        self.assertEqual(self.client.get(self.projects_url).status_code, 403)

        token = self.login().data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(self.projects_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({item["customer"]["email"] for item in response.data}, {"anna@example.com", "boris@example.com"})
        self.assertEqual({item["configuration"]["height_cm"] for item in response.data}, {40, 50})
        self.assertEqual(SavedProject.objects.count(), 2)

    def test_password_change_and_staff_revocation_invalidate_token(self):
        token = self.login().data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.user.set_password("updated-test-password")
        self.user.save(update_fields=("password",))
        self.assertEqual(self.client.get(self.briefs_url).status_code, 403)

        replacement = self.login("updated-test-password").data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {replacement}")
        self.user.is_staff = False
        self.user.save(update_fields=("is_staff",))
        self.assertEqual(self.client.get(self.briefs_url).status_code, 403)

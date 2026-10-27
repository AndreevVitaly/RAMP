from django.contrib.auth.hashers import check_password
from rest_framework.test import APITestCase

from ramps.accounts import issue_session
from ramps.models import Customer, CustomerAuthAttempt


class PasswordAuthTests(APITestCase):
    register_url = "/api/ramp/account/register/"
    login_url = "/api/ramp/account/login/"

    def test_register_login_and_access_saved_projects_without_email_delivery(self):
        response = self.client.post(self.register_url, {
            "name": " Анна ", "email": " Anna@Example.com ", "password": "long-password-123",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        customer = Customer.objects.get()
        self.assertEqual((customer.name, customer.email), ("Анна", "anna@example.com"))
        self.assertTrue(check_password("long-password-123", customer.password_hash))
        self.assertNotEqual(customer.password_hash, "long-password-123")
        self.assertFalse(customer.email_verified)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['token']}")
        self.assertEqual(self.client.get("/api/ramp/account/projects/").status_code, 200)

        self.client.credentials()
        login = self.client.post(self.login_url, {
            "email": "ANNA@example.com", "password": "long-password-123",
        }, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data["customer"]["id"], customer.pk)

    def test_duplicate_email_does_not_replace_existing_password(self):
        customer = Customer.objects.create(name="Анна", email="anna@example.com", password_hash="stored-hash")
        response = self.client.post(self.register_url, {
            "name": "Другая", "email": "ANNA@EXAMPLE.COM", "password": "another-password",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        customer.refresh_from_db()
        self.assertEqual(customer.password_hash, "stored-hash")
        self.assertEqual(Customer.objects.count(), 1)

    def test_wrong_password_and_old_account_without_password_are_rejected(self):
        Customer.objects.create(name="Старый клиент", email="old@example.com")
        for password in ("incorrect-password", ""):
            response = self.client.post(self.login_url, {
                "email": "old@example.com", "password": password,
            }, format="json")
            self.assertEqual(response.status_code, 400)

    def test_login_attempts_are_limited(self):
        for _ in range(10):
            response = self.client.post(self.login_url, {
                "email": "nobody@example.com", "password": "wrong-password",
            }, format="json")
            self.assertEqual(response.status_code, 400)
        response = self.client.post(self.login_url, {
            "email": "nobody@example.com", "password": "wrong-password",
        }, format="json")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(CustomerAuthAttempt.objects.count(), 10)

    def test_existing_code_account_can_set_password_with_its_session(self):
        customer = Customer.objects.create(name="Старый клиент", email="old@example.com", email_verified=True)
        token = issue_session(customer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertFalse(self.client.get("/api/ramp/account/me/").data["has_password"])
        response = self.client.post("/api/ramp/account/password/", {"new_password": "new-password-123"}, format="json")
        self.assertEqual(response.status_code, 200)
        customer.refresh_from_db()
        self.assertTrue(check_password("new-password-123", customer.password_hash))
        self.assertTrue(self.client.get("/api/ramp/account/me/").data["has_password"])
        self.client.credentials()
        self.assertEqual(self.client.post(self.login_url, {
            "email": customer.email, "password": "new-password-123",
        }, format="json").status_code, 200)

    def test_password_change_requires_current_password(self):
        registration = self.client.post(self.register_url, {
            "name": "Анна", "email": "anna@example.com", "password": "long-password-123",
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {registration.data['token']}")
        response = self.client.post("/api/ramp/account/password/", {
            "current_password": "wrong", "new_password": "new-password-123",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/api/ramp/account/password/", {
            "current_password": "long-password-123", "new_password": "new-password-123",
        }, format="json")
        self.assertEqual(response.status_code, 200)

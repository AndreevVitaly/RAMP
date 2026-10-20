from django.test import override_settings
from rest_framework.test import APITestCase

from ramps.models import Customer


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True)
class EmailRegistrationTests(APITestCase):
    def register(self, email, phone=None):
        payload = {"name": "Анна", "email": email}
        if phone is not None:
            payload["phone"] = phone
        requested = self.client.post("/api/ramp/account/request-code/", payload, format="json")
        self.assertEqual(requested.status_code, 200)
        return self.client.post("/api/ramp/account/verify-code/", {"email": email, "code": requested.data["dev_code"]}, format="json")

    def test_phone_can_be_omitted_for_multiple_customers(self):
        for email in ("anna@example.com", "boris@example.com"):
            verified = self.register(email)
            self.assertEqual(verified.status_code, 200)
            self.assertIsNone(verified.data["customer"]["phone"])
        self.assertEqual(Customer.objects.count(), 2)

    def test_repeat_email_login_reuses_customer_without_phone(self):
        self.register("anna@example.com")
        self.assertEqual(self.register("anna@example.com").status_code, 200)
        self.assertEqual(Customer.objects.count(), 1)

    def test_omitting_phone_does_not_erase_existing_number(self):
        self.assertEqual(self.register("anna@example.com", "+7 900 000-00-00").status_code, 200)
        self.assertEqual(self.register("anna@example.com").status_code, 200)
        self.assertEqual(Customer.objects.get(email="anna@example.com").phone, "+79000000000")

    def test_invalid_supplied_phone_is_rejected(self):
        response = self.client.post("/api/ramp/account/request-code/", {"name": "Анна", "email": "anna@example.com", "phone": "123"}, format="json")
        self.assertEqual(response.status_code, 400)

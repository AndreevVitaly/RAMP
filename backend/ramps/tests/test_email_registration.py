from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from ramps.models import Customer, PhoneVerification


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True,
                   EMAIL_CODE_COOLDOWN_SECONDS=0, EMAIL_CODE_EMAIL_HOURLY_LIMIT=100, EMAIL_CODE_IP_HOURLY_LIMIT=100)
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

    def test_existing_customer_logs_in_with_email_only(self):
        first = self.register("anna@example.com", "+7 900 000-00-00")
        customer_id = first.data["customer"]["id"]
        requested = self.client.post("/api/ramp/account/login/request-code/", {"email": "ANNA@example.com"}, format="json")
        self.assertEqual(requested.status_code, 200)
        self.assertIn("dev_code", requested.data)
        self.assertEqual(PhoneVerification.objects.get().purpose, PhoneVerification.LOGIN)
        self.assertEqual(mail.outbox[-1].to, ["anna@example.com"])
        verified = self.client.post("/api/ramp/account/verify-code/", {"email": "anna@example.com", "code": requested.data["dev_code"]}, format="json")
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(verified.data["customer"]["id"], customer_id)
        self.assertEqual(verified.data["customer"]["name"], "Анна")
        self.assertEqual(verified.data["customer"]["phone"], "+79000000000")
        self.assertEqual(Customer.objects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {verified.data['token']}")
        self.assertEqual(self.client.get("/api/ramp/account/me/").status_code, 200)

    def test_unknown_email_does_not_create_account_or_send_code(self):
        requested = self.client.post("/api/ramp/account/login/request-code/", {"email": "missing@example.com"}, format="json")
        self.assertEqual(requested.status_code, 200)
        self.assertNotIn("dev_code", requested.data)
        self.assertEqual(Customer.objects.count(), 0)
        self.assertEqual(PhoneVerification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_unverified_account_cannot_log_in(self):
        Customer.objects.create(name="Анна", email="anna@example.com", email_verified=False)
        requested = self.client.post("/api/ramp/account/login/request-code/", {"email": "anna@example.com"}, format="json")
        self.assertEqual(requested.status_code, 200)
        self.assertNotIn("dev_code", requested.data)
        self.assertEqual(PhoneVerification.objects.count(), 0)

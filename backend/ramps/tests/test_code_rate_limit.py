from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from ramps.models import Customer, EmailCodeRequest, PhoneVerification


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True)
class EmailCodeRateLimitTests(APITestCase):
    def request_code(self, email, ip="127.0.0.1"):
        return self.client.post(
            "/api/ramp/account/request-code/",
            {"name": "Анна", "email": email}, format="json", REMOTE_ADDR=ip,
        )

    def test_cooldown_applies_across_registration_and_login(self):
        Customer.objects.create(name="Анна", email="anna@example.com", email_verified=True)
        self.assertEqual(self.request_code("anna@example.com").status_code, 200)
        second = self.client.post(
            "/api/ramp/account/login/request-code/",
            {"email": "ANNA@example.com"}, format="json", REMOTE_ADDR="127.0.0.1",
        )
        self.assertEqual(second.status_code, 429)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(PhoneVerification.objects.count(), 1)

    @override_settings(EMAIL_CODE_COOLDOWN_SECONDS=0, EMAIL_CODE_EMAIL_HOURLY_LIMIT=2)
    def test_email_hourly_limit(self):
        self.assertEqual(self.request_code("anna@example.com").status_code, 200)
        self.assertEqual(self.request_code("anna@example.com").status_code, 200)
        self.assertEqual(self.request_code("anna@example.com").status_code, 429)
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(EMAIL_CODE_COOLDOWN_SECONDS=0, EMAIL_CODE_IP_HOURLY_LIMIT=2)
    def test_ip_hourly_limit(self):
        self.assertEqual(self.request_code("anna@example.com").status_code, 200)
        self.assertEqual(self.request_code("boris@example.com").status_code, 200)
        self.assertEqual(self.request_code("vera@example.com").status_code, 429)
        self.assertEqual(EmailCodeRequest.objects.count(), 2)

    @override_settings(DEBUG=False, EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_production_console_email_fails_before_creating_code(self):
        self.assertEqual(self.request_code("anna@example.com").status_code, 503)
        self.assertEqual(PhoneVerification.objects.count(), 0)

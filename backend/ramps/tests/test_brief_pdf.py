from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from ramps.accounts import issue_session
from ramps.models import AdminContactSettings, Customer, TechnicalBrief


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TechnicalBriefPdfTests(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Анна", email="anna@example.com", phone="+79000000000", email_verified=True)
        self.token = issue_session(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        AdminContactSettings.objects.create(email="master@example.com")

    def test_pdf_is_sent_to_both_and_can_be_downloaded(self):
        response = self.client.post("/api/ramp/account/briefs/pdf/", {
            "configuration": {"height_cm": 50, "ramp_length_cm": 100, "width_cm": 40, "color": "beige", "has_slats": True},
            "message": "Ширина дверного проёма 45 см",
            "result": {"price": {"total_price_rub": 1}},
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["delivery_status"], {"admin": "sent", "customer": "sent"})
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual({mail.outbox[0].to[0], mail.outbox[1].to[0]}, {"master@example.com", "anna@example.com"})
        self.assertEqual(mail.outbox[0].attachments[0][1], mail.outbox[1].attachments[0][1])
        self.assertTrue(mail.outbox[0].attachments[0][1].startswith(b"%PDF-"))
        brief = TechnicalBrief.objects.get(pk=response.data["id"])
        self.assertEqual(brief.result["price"]["total_price_rub"], 2000)
        downloaded = self.client.get(response.data["download_url"])
        self.assertEqual(downloaded.status_code, 200)
        self.assertTrue(downloaded.content.startswith(b"%PDF-"))
        self.assertEqual(downloaded["Content-Type"], "application/pdf")

    def test_requires_admin_address_and_customer_login(self):
        AdminContactSettings.objects.update(email="")
        response = self.client.post("/api/ramp/account/briefs/pdf/", {"configuration": {"height_cm": 50}}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TechnicalBrief.objects.count(), 0)
        self.client.credentials()
        response = self.client.post("/api/ramp/account/briefs/pdf/", {"configuration": {"height_cm": 50}}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_other_customer_cannot_download_pdf(self):
        brief = TechnicalBrief.objects.create(customer=self.customer, configuration={}, result={}, requested_channels=[])
        other = Customer.objects.create(name="Другой", email="other@example.com", phone="+79000000001", email_verified=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_session(other)}")
        self.assertEqual(self.client.get(f"/api/ramp/account/briefs/{brief.pk}/pdf/").status_code, 404)

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ramps.models import AdminContactSettings, Customer


class DjangoAdminTests(TestCase):
    def test_anonymous_user_is_redirected_to_admin_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_superuser_can_open_project_models(self):
        superuser = get_user_model().objects.create_superuser("operator", "operator@example.com", "test-password")
        self.client.force_login(superuser)
        index = self.client.get(reverse("admin:index"))
        self.assertContains(index, "Пандусы RAMP")
        self.assertContains(index, "Контакты администратора")
        self.assertContains(index, "Клиенты")
        self.assertContains(index, "Изображения пандусов")
        self.assertContains(index, "Технические задания")
        self.assertContains(index, "Управление RAMP")
        self.assertContains(index, "admin/css/ramp_admin.css")
        for model in ("customer", "technicalbrief", "rampimage", "admincontactsettings"):
            with self.subTest(model=model):
                response = self.client.get(reverse(f"admin:ramps_{model}_changelist"))
                self.assertEqual(response.status_code, 200)

    def test_contacts_remain_singleton_in_admin(self):
        AdminContactSettings.objects.create(email="master@example.com")
        superuser = get_user_model().objects.create_superuser("operator", "operator@example.com", "test-password")
        self.client.force_login(superuser)
        self.assertEqual(self.client.get(reverse("admin:ramps_admincontactsettings_add")).status_code, 403)

    def test_customer_cannot_be_changed_in_admin(self):
        customer = Customer.objects.create(name="Анна", email="anna@example.com", email_verified=True)
        superuser = get_user_model().objects.create_superuser("operator", "operator@example.com", "test-password")
        self.client.force_login(superuser)
        response = self.client.post(reverse("admin:ramps_customer_change", args=[customer.pk]), {"name": "Изменено"})
        self.assertEqual(response.status_code, 403)
        customer.refresh_from_db()
        self.assertEqual(customer.name, "Анна")

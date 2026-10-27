from django.contrib import admin
from django import forms
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .accounts import digest
from .models import AdminContactSettings, Customer, CustomerAuthAttempt, CustomerSession, RampImage, SavedProject, TechnicalBrief


admin.site.site_header = "RAMP — администрирование"
admin.site.site_title = "Администрирование RAMP"
admin.site.index_title = "Данные проекта"


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdminContactSettings)
class AdminContactSettingsAdmin(admin.ModelAdmin):
    list_display = ("email", "phone", "preferred_channel", "updated_at")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not AdminContactSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class CustomerPasswordResetForm(forms.Form):
    password = forms.CharField(
        label="Новый временный пароль",
        min_length=10,
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    confirmation = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") and cleaned.get("confirmation") and cleaned["password"] != cleaned["confirmation"]:
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned


@admin.register(Customer)
class CustomerAdmin(ReadOnlyAdmin):
    list_display = ("name", "email", "phone", "email_verified", "created_at")
    search_fields = ("name", "email", "phone")
    list_filter = ("email_verified", "created_at")

    def get_list_display(self, request):
        fields = super().get_list_display(request)
        return (*fields, "password_reset_link") if request.user.is_superuser else fields

    @admin.display(description="Помощь со входом")
    def password_reset_link(self, obj):
        url = reverse("admin:ramps_customer_reset_password", args=[obj.pk])
        return format_html('<a href="{}">Задать новый пароль</a>', url)

    def get_urls(self):
        custom = [
            path("<int:customer_id>/reset-password/", self.admin_site.admin_view(self.reset_password), name="ramps_customer_reset_password"),
        ]
        return custom + super().get_urls()

    def reset_password(self, request, customer_id):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        customer = self.get_object(request, str(customer_id))
        if customer is None:
            from django.http import Http404
            raise Http404
        form = CustomerPasswordResetForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            customer.password_hash = make_password(form.cleaned_data["password"])
            customer.save(update_fields=["password_hash", "updated_at"])
            CustomerSession.objects.filter(customer=customer).delete()
            CustomerAuthAttempt.objects.filter(purpose="login", email_digest=digest(f"email:{customer.email.strip().lower()}")).delete()
            self.message_user(request, "Новый пароль сохранён. Передайте его клиенту лично; прежние сеансы завершены.", messages.SUCCESS)
            return HttpResponseRedirect(reverse("admin:ramps_customer_changelist"))
        context = {
            **self.admin_site.each_context(request),
            "title": f"Новый пароль для {customer.name}",
            "customer": customer,
            "form": form,
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/ramps/customer/reset_password.html", context)


@admin.register(TechnicalBrief)
class TechnicalBriefAdmin(ReadOnlyAdmin):
    list_display = ("id", "customer", "created_at", "requested_channels", "delivery_status")
    search_fields = ("customer__name", "customer__email", "message")
    list_select_related = ("customer",)
    list_filter = ("created_at",)


@admin.register(SavedProject)
class SavedProjectAdmin(ReadOnlyAdmin):
    list_display = ("id", "project_link", "customer", "updated_at")
    list_display_links = None
    search_fields = ("name", "customer__name", "customer__email")
    list_select_related = ("customer",)
    list_filter = ("created_at",)

    @admin.display(description="Название", ordering="name")
    def project_link(self, obj):
        return format_html('<a href="/?admin_project={}">{}</a>', obj.pk, obj.name)


@admin.register(RampImage)
class RampImageAdmin(ReadOnlyAdmin):
    list_display = ("id", "kind", "title", "image_type", "color", "is_primary", "created_at")
    search_fields = ("title", "caption", "original_name")
    list_filter = ("kind", "image_type", "color", "is_primary")

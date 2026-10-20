from django.contrib import admin

from .models import AdminContactSettings, Customer, RampImage, TechnicalBrief


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


@admin.register(Customer)
class CustomerAdmin(ReadOnlyAdmin):
    list_display = ("name", "email", "phone", "email_verified", "created_at")
    search_fields = ("name", "email", "phone")
    list_filter = ("email_verified", "created_at")


@admin.register(TechnicalBrief)
class TechnicalBriefAdmin(ReadOnlyAdmin):
    list_display = ("id", "customer", "created_at", "requested_channels", "delivery_status")
    search_fields = ("customer__name", "customer__email", "message")
    list_select_related = ("customer",)
    list_filter = ("created_at",)


@admin.register(RampImage)
class RampImageAdmin(ReadOnlyAdmin):
    list_display = ("id", "kind", "title", "image_type", "color", "is_primary", "created_at")
    search_fields = ("title", "caption", "original_name")
    list_filter = ("kind", "image_type", "color", "is_primary")

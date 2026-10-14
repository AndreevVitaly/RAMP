from django.urls import path
from .views import AdminBriefListView, AdminSettingsView, CustomerAccountView, RampCalculationView, RampImageDetailView, RampImageListCreateView, RequestPhoneCodeView, TechnicalBriefListCreateView, VerifyPhoneCodeView

urlpatterns = [
    path("calculate/", RampCalculationView.as_view(), name="ramp-calculate"),
    path("images/", RampImageListCreateView.as_view(), name="ramp-images"),
    path("images/<int:pk>/", RampImageDetailView.as_view(), name="ramp-image-detail"),
    path("account/request-code/", RequestPhoneCodeView.as_view(), name="request-phone-code"),
    path("account/verify-code/", VerifyPhoneCodeView.as_view(), name="verify-phone-code"),
    path("account/me/", CustomerAccountView.as_view(), name="customer-account"),
    path("account/briefs/", TechnicalBriefListCreateView.as_view(), name="technical-briefs"),
    path("admin/settings/", AdminSettingsView.as_view(), name="admin-settings"),
    path("admin/briefs/", AdminBriefListView.as_view(), name="admin-briefs"),
]


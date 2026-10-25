from django.urls import path
from .views import AdminBriefListView, AdminLoginView, AdminSavedProjectListView, AdminSettingsView, CustomerAccountView, RampCalculationView, RampImageDetailView, RampImageListCreateView, RequestEmailCodeView, RequestLoginCodeView, SavedProjectListCreateView, TechnicalBriefListCreateView, TechnicalBriefPdfView, TechnicalBriefPdfDownloadView, VerifyEmailCodeView

urlpatterns = [
    path("calculate/", RampCalculationView.as_view(), name="ramp-calculate"),
    path("images/", RampImageListCreateView.as_view(), name="ramp-images"),
    path("images/<int:pk>/", RampImageDetailView.as_view(), name="ramp-image-detail"),
    path("account/request-code/", RequestEmailCodeView.as_view(), name="request-email-code"),
    path("account/login/request-code/", RequestLoginCodeView.as_view(), name="request-login-code"),
    path("account/verify-code/", VerifyEmailCodeView.as_view(), name="verify-email-code"),
    path("account/me/", CustomerAccountView.as_view(), name="customer-account"),
    path("account/projects/", SavedProjectListCreateView.as_view(), name="saved-projects"),
    path("account/briefs/", TechnicalBriefListCreateView.as_view(), name="technical-briefs"),
    path("account/briefs/pdf/", TechnicalBriefPdfView.as_view(), name="technical-brief-pdf"),
    path("account/briefs/<int:pk>/pdf/", TechnicalBriefPdfDownloadView.as_view(), name="technical-brief-pdf-download"),
    path("admin/settings/", AdminSettingsView.as_view(), name="admin-settings"),
    path("admin/briefs/", AdminBriefListView.as_view(), name="admin-briefs"),
    path("admin/projects/", AdminSavedProjectListView.as_view(), name="admin-projects"),
    path("admin/login/", AdminLoginView.as_view(), name="admin-login"),
]


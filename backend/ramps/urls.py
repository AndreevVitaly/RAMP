from django.urls import path
from .views import AdminBriefListView, AdminLoginView, AdminSavedProjectListView, AdminSavedProjectStatusView, AdminSettingsView, CustomerAccountView, CustomerPasswordLoginView, CustomerPasswordView, CustomerRegisterView, RampCalculationView, RampImageDetailView, RampImageListCreateView, RequestEmailCodeView, RequestLoginCodeView, SavedProjectDetailView, SavedProjectListCreateView, SavedProjectSubmitView, TechnicalBriefListCreateView, TechnicalBriefPdfView, TechnicalBriefPdfPreviewView, TechnicalBriefPdfDownloadView, VerifyEmailCodeView, django_admin_project_preview

urlpatterns = [
    path("calculate/", RampCalculationView.as_view(), name="ramp-calculate"),
    path("images/", RampImageListCreateView.as_view(), name="ramp-images"),
    path("images/<int:pk>/", RampImageDetailView.as_view(), name="ramp-image-detail"),
    path("account/register/", CustomerRegisterView.as_view(), name="customer-register"),
    path("account/login/", CustomerPasswordLoginView.as_view(), name="customer-password-login"),
    path("account/request-code/", RequestEmailCodeView.as_view(), name="request-email-code"),
    path("account/login/request-code/", RequestLoginCodeView.as_view(), name="request-login-code"),
    path("account/verify-code/", VerifyEmailCodeView.as_view(), name="verify-email-code"),
    path("account/me/", CustomerAccountView.as_view(), name="customer-account"),
    path("account/password/", CustomerPasswordView.as_view(), name="customer-password"),
    path("account/projects/", SavedProjectListCreateView.as_view(), name="saved-projects"),
    path("account/projects/<int:pk>/", SavedProjectDetailView.as_view(), name="saved-project-detail"),
    path("account/projects/<int:pk>/submit/", SavedProjectSubmitView.as_view(), name="saved-project-submit"),
    path("account/briefs/", TechnicalBriefListCreateView.as_view(), name="technical-briefs"),
    path("account/briefs/pdf/", TechnicalBriefPdfView.as_view(), name="technical-brief-pdf"),
    path("account/briefs/pdf/download/", TechnicalBriefPdfPreviewView.as_view(), name="technical-brief-pdf-preview"),
    path("account/briefs/<int:pk>/pdf/", TechnicalBriefPdfDownloadView.as_view(), name="technical-brief-pdf-download"),
    path("admin/settings/", AdminSettingsView.as_view(), name="admin-settings"),
    path("admin/briefs/", AdminBriefListView.as_view(), name="admin-briefs"),
    path("admin/projects/", AdminSavedProjectListView.as_view(), name="admin-projects"),
    path("admin/projects/<int:pk>/status/", AdminSavedProjectStatusView.as_view(), name="admin-project-status"),
    path("admin/projects/<int:pk>/preview/", django_admin_project_preview, name="django-admin-project-preview"),
    path("admin/login/", AdminLoginView.as_view(), name="admin-login"),
]


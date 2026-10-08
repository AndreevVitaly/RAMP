from django.urls import path
from .views import RampCalculationView, RampImageDetailView, RampImageListCreateView

urlpatterns = [
    path("calculate/", RampCalculationView.as_view(), name="ramp-calculate"),
    path("images/", RampImageListCreateView.as_view(), name="ramp-images"),
    path("images/<int:pk>/", RampImageDetailView.as_view(), name="ramp-image-detail"),
]


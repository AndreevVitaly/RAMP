from django.urls import path
from .views import RampCalculationView

urlpatterns = [path("calculate/", RampCalculationView.as_view(), name="ramp-calculate")]


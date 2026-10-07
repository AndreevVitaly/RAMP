from django.urls import include, path

urlpatterns = [path("api/ramp/", include("ramps.urls"))]


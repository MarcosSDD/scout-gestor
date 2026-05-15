from django.urls import include, path

from api.v1.views import HealthCheckView, ProtectedPingView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("protected/ping/", ProtectedPingView.as_view(), name="protected-ping"),
    path("auth/", include("api.v1.auth.urls")),
    path("catalogos/", include("api.v1.catalogos.urls")),
]

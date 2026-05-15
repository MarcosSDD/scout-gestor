from django.urls import include, path

from api.v1.views import HealthCheckView, ProtectedPingView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("protected/ping/", ProtectedPingView.as_view(), name="protected-ping"),
    path("auth/", include("api.v1.auth.urls")),
    path("catalogos/", include("api.v1.catalogos.urls")),
    path("grupos/", include("api.v1.organizacion.urls")),
    path("personas/", include("api.v1.personas.urls")),
    path("unidades/", include("api.v1.unidades.urls")),
    path("formacion/", include("api.v1.formacion.urls")),
]

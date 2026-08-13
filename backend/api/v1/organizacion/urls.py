from django.urls import path

from api.v1.organizacion.views import (
    GrupoScoutCalcularMinimoView,
    GrupoScoutEstructuraView,
    GrupoScoutListCreateView,
    GrupoScoutRetrieveUpdateView,
)

urlpatterns = [
    path("", GrupoScoutListCreateView.as_view(), name="grupos-list"),
    path("<int:pk>/", GrupoScoutRetrieveUpdateView.as_view(), name="grupos-detail"),
    path("<int:pk>/calcular-minimo/", GrupoScoutCalcularMinimoView.as_view(), name="grupos-calcular-minimo"),
    path("<int:pk>/estructura/", GrupoScoutEstructuraView.as_view(), name="grupos-estructura"),
]

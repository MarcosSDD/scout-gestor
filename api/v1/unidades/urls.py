from django.urls import path

from api.v1.unidades.views import (
    AdultoUnidadRolListCreateView,
    AdultoUnidadRolRetrieveUpdateView,
    SubgrupoListCreateView,
    SubgrupoMiembroListCreateView,
    SubgrupoMiembroRetrieveUpdateView,
    SubgrupoMiembroReasignacionView,
    SubgrupoRetrieveUpdateView,
    UnidadListCreateView,
    UnidadRetrieveUpdateView,
    OpcionesGruposView,
    OpcionesBeneficiariosView,
    OpcionesAdultosView,
    OpcionesDestinosMembresiaView,
)

urlpatterns = [
    path("", UnidadListCreateView.as_view(), name="unidades-list"),
    path("<int:pk>/", UnidadRetrieveUpdateView.as_view(), name="unidades-detail"),
    path("adultos-roles/", AdultoUnidadRolListCreateView.as_view(), name="unidades-adultos-roles-list"),
    path(
        "adultos-roles/<int:pk>/",
        AdultoUnidadRolRetrieveUpdateView.as_view(),
        name="unidades-adultos-roles-detail",
    ),
    path("subgrupos/", SubgrupoListCreateView.as_view(), name="subgrupos-list"),
    path("subgrupos/<int:pk>/", SubgrupoRetrieveUpdateView.as_view(), name="subgrupos-detail"),
    path("subgrupos-miembros/", SubgrupoMiembroListCreateView.as_view(), name="subgrupos-miembros-list"),
    path(
        "subgrupos-miembros/<int:pk>/",
        SubgrupoMiembroRetrieveUpdateView.as_view(),
        name="subgrupos-miembros-detail",
    ),
    path(
        "subgrupos-miembros/<int:pk>/reasignacion/",
        SubgrupoMiembroReasignacionView.as_view(),
        name="subgrupos-miembros-reasignacion",
    ),
    path("opciones/grupos/", OpcionesGruposView.as_view(), name="unidades-opciones-grupos"),
    path("opciones/beneficiarios/", OpcionesBeneficiariosView.as_view(), name="unidades-opciones-beneficiarios"),
    path("opciones/adultos/", OpcionesAdultosView.as_view(), name="unidades-opciones-adultos"),
    path("opciones/destinos-membresia/", OpcionesDestinosMembresiaView.as_view(), name="unidades-opciones-destinos-membresia"),
]

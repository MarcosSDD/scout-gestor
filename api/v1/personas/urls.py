from django.urls import path

from api.v1.personas.views import (
    AdultoListCreateView,
    AdultoRetrieveUpdateView,
    ApoderadoBeneficiarioListCreateView,
    ApoderadoBeneficiarioRetrieveUpdateView,
    ApoderadoListCreateView,
    ApoderadoRetrieveUpdateView,
    BeneficiarioListCreateView,
    BeneficiarioRetrieveUpdateView,
    PersonaListCreateView,
    PersonaRetrieveUpdateView,
    ValidarRutView,
)

urlpatterns = [
    path("", PersonaListCreateView.as_view(), name="personas-list"),
    path("validar-rut/", ValidarRutView.as_view(), name="personas-validar-rut"),
    path("<int:pk>/", PersonaRetrieveUpdateView.as_view(), name="personas-detail"),
    path("adultos/", AdultoListCreateView.as_view(), name="adultos-list"),
    path("adultos/<int:pk>/", AdultoRetrieveUpdateView.as_view(), name="adultos-detail"),
    path("beneficiarios/", BeneficiarioListCreateView.as_view(), name="beneficiarios-list"),
    path("beneficiarios/<int:pk>/", BeneficiarioRetrieveUpdateView.as_view(), name="beneficiarios-detail"),
    path("apoderados/", ApoderadoListCreateView.as_view(), name="apoderados-list"),
    path("apoderados/<int:pk>/", ApoderadoRetrieveUpdateView.as_view(), name="apoderados-detail"),
    path(
        "apoderados-beneficiarios/",
        ApoderadoBeneficiarioListCreateView.as_view(),
        name="apoderados-beneficiarios-list",
    ),
    path(
        "apoderados-beneficiarios/<int:pk>/",
        ApoderadoBeneficiarioRetrieveUpdateView.as_view(),
        name="apoderados-beneficiarios-detail",
    ),
]

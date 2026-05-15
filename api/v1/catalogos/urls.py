from django.urls import path

from api.v1.catalogos.views import DistritoListView, RamaListView, ZonaListView

urlpatterns = [
    path("zonas/", ZonaListView.as_view(), name="catalogos-zonas"),
    path("distritos/", DistritoListView.as_view(), name="catalogos-distritos"),
    path("ramas/", RamaListView.as_view(), name="catalogos-ramas"),
]

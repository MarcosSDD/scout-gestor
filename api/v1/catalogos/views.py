from rest_framework.generics import ListAPIView

from api.v1.catalogos.serializers import DistritoSerializer, RamaSerializer, ZonaSerializer
from api.v1.responses import success_response
from catalogos.models import Distrito, Rama, Zona


class CatalogListBaseView(ListAPIView):
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            meta = {
                "count": paginated_response.data["count"],
                "next": paginated_response.data["next"],
                "previous": paginated_response.data["previous"],
            }
            return success_response(data=serializer.data, meta=meta)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


class ZonaListView(CatalogListBaseView):
    serializer_class = ZonaSerializer

    def get_queryset(self):
        queryset = Zona.objects.order_by("nombre")
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(nombre__icontains=search.strip())
        return queryset


class DistritoListView(CatalogListBaseView):
    serializer_class = DistritoSerializer

    def get_queryset(self):
        queryset = Distrito.objects.select_related("zona").order_by("nombre")

        zona_id = self.request.query_params.get("zona_id")
        if zona_id:
            queryset = queryset.filter(zona_id=zona_id)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(nombre__icontains=search.strip())

        return queryset


class RamaListView(CatalogListBaseView):
    serializer_class = RamaSerializer

    def get_queryset(self):
        queryset = Rama.objects.order_by("edad_minima", "nombre")

        activa = self.request.query_params.get("activa")
        if activa:
            activa_normalized = activa.lower().strip()
            if activa_normalized in {"true", "1", "yes", "si"}:
                queryset = queryset.filter(activa=True)
            elif activa_normalized in {"false", "0", "no"}:
                queryset = queryset.filter(activa=False)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(nombre__icontains=search.strip())

        return queryset

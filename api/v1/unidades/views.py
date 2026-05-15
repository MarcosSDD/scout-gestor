from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView

from api.v1.responses import success_response
from api.v1.unidades.serializers import (
    AdultoUnidadRolListSerializer,
    AdultoUnidadRolWriteSerializer,
    SubgrupoListSerializer,
    SubgrupoMiembroListSerializer,
    SubgrupoMiembroWriteSerializer,
    SubgrupoWriteSerializer,
    UnidadDetailSerializer,
    UnidadListSerializer,
    UnidadWriteSerializer,
)
from unidades.models import AdultoUnidadRol, Subgrupo, SubgrupoMiembro, Unidad


class _ListResponseMixin:
    def _list_response(self, queryset, serializer_class):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            meta = {
                "count": paginated_response.data["count"],
                "next": paginated_response.data["next"],
                "previous": paginated_response.data["previous"],
            }
            return success_response(data=serializer.data, meta=meta)

        serializer = serializer_class(queryset, many=True)
        return success_response(data=serializer.data)


class UnidadListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Unidad.objects.select_related("grupo", "rama").order_by("nombre")

    def get(self, request):
        queryset = self.get_queryset()

        grupo_id = request.query_params.get("grupo_id")
        if grupo_id:
            queryset = queryset.filter(grupo_id=grupo_id)

        rama_id = request.query_params.get("rama_id")
        if rama_id:
            queryset = queryset.filter(rama_id=rama_id)

        estado = request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(estado=estado)

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(nombre__icontains=search.strip())

        return self._list_response(queryset, UnidadListSerializer)

    def post(self, request):
        serializer = UnidadWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = UnidadDetailSerializer(instance).data
        return success_response(data=payload, message="Unidad creada", status_code=status.HTTP_201_CREATED)


class UnidadRetrieveUpdateView(GenericAPIView):
    queryset = Unidad.objects.select_related("grupo", "rama")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = UnidadDetailSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = UnidadWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = UnidadDetailSerializer(instance).data
        return success_response(data=payload, message="Unidad actualizada")


class AdultoUnidadRolListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = AdultoUnidadRol.objects.select_related("unidad", "adulto__persona").order_by("unidad__nombre", "rol")

    def get(self, request):
        queryset = self.get_queryset()

        unidad_id = request.query_params.get("unidad_id")
        if unidad_id:
            queryset = queryset.filter(unidad_id=unidad_id)

        adulto_id = request.query_params.get("adulto_id")
        if adulto_id:
            queryset = queryset.filter(adulto_id=adulto_id)

        return self._list_response(queryset, AdultoUnidadRolListSerializer)

    def post(self, request):
        serializer = AdultoUnidadRolWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = AdultoUnidadRolListSerializer(instance).data
        return success_response(data=payload, message="Asignacion creada", status_code=status.HTTP_201_CREATED)


class AdultoUnidadRolRetrieveUpdateView(GenericAPIView):
    queryset = AdultoUnidadRol.objects.select_related("unidad", "adulto__persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = AdultoUnidadRolListSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = AdultoUnidadRolWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = AdultoUnidadRolListSerializer(instance).data
        return success_response(data=payload, message="Asignacion actualizada")


class SubgrupoListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Subgrupo.objects.select_related("unidad", "lider_juvenil__persona").order_by("unidad__nombre", "nombre")

    def get(self, request):
        queryset = self.get_queryset()

        unidad_id = request.query_params.get("unidad_id")
        if unidad_id:
            queryset = queryset.filter(unidad_id=unidad_id)

        return self._list_response(queryset, SubgrupoListSerializer)

    def post(self, request):
        serializer = SubgrupoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = SubgrupoListSerializer(instance).data
        return success_response(data=payload, message="Subgrupo creado", status_code=status.HTTP_201_CREATED)


class SubgrupoRetrieveUpdateView(GenericAPIView):
    queryset = Subgrupo.objects.select_related("unidad", "lider_juvenil__persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = SubgrupoListSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = SubgrupoWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = SubgrupoListSerializer(instance).data
        return success_response(data=payload, message="Subgrupo actualizado")


class SubgrupoMiembroListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = SubgrupoMiembro.objects.select_related("subgrupo", "beneficiario__persona").order_by(
        "subgrupo__nombre",
        "beneficiario__persona__apellidos",
    )

    def get(self, request):
        queryset = self.get_queryset()

        subgrupo_id = request.query_params.get("subgrupo_id")
        if subgrupo_id:
            queryset = queryset.filter(subgrupo_id=subgrupo_id)

        beneficiario_id = request.query_params.get("beneficiario_id")
        if beneficiario_id:
            queryset = queryset.filter(beneficiario_id=beneficiario_id)

        return self._list_response(queryset, SubgrupoMiembroListSerializer)

    def post(self, request):
        serializer = SubgrupoMiembroWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = SubgrupoMiembroListSerializer(instance).data
        return success_response(data=payload, message="Miembro asignado", status_code=status.HTTP_201_CREATED)


class SubgrupoMiembroRetrieveUpdateView(GenericAPIView):
    queryset = SubgrupoMiembro.objects.select_related("subgrupo", "beneficiario__persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = SubgrupoMiembroListSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = SubgrupoMiembroWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = SubgrupoMiembroListSerializer(instance).data
        return success_response(data=payload, message="Miembro actualizado")

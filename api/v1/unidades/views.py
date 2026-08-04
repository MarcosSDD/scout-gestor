from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView

from api.v1.access import (
    can_edit_unidad,
    can_manage_group_data,
    get_accessible_adultos_qs,
    get_accessible_subgrupo_miembros_qs,
    get_accessible_subgrupos_qs,
    get_accessible_unidades_qs,
    get_editable_unidad_ids,
    get_unidad_detail_permissions,
)
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


def _reject_immutable_relationships(request, fields):
    prohibited = set(request.data) & set(fields)
    if prohibited:
        raise ValidationError({field: "Esta relacion no puede modificarse por este endpoint" for field in prohibited})


class UnidadListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Unidad.objects.select_related("grupo", "rama").order_by("nombre")

    def get_queryset(self):
        return get_accessible_unidades_qs(self.request.user).select_related("grupo", "rama").order_by("nombre")

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
        grupo_id = request.data.get("grupo")
        if not grupo_id:
            raise PermissionDenied("Debe indicar grupo para crear unidad")
        if not can_manage_group_data(request.user, int(grupo_id)):
            raise PermissionDenied("No tiene permisos para crear unidades en este grupo")
        serializer = UnidadWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = UnidadDetailSerializer(instance).data
        return success_response(data=payload, message="Unidad creada", status_code=status.HTTP_201_CREATED)


class UnidadRetrieveUpdateView(GenericAPIView):
    queryset = Unidad.objects.select_related("grupo", "rama")

    def get_queryset(self):
        return get_accessible_unidades_qs(self.request.user).select_related("grupo", "rama")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = UnidadDetailSerializer(instance)
        return success_response(data=serializer.data, meta={"permissions": get_unidad_detail_permissions(request.user, instance)})

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_unidad(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar esta unidad")
        _reject_immutable_relationships(request, {"grupo", "rama"})
        serializer = UnidadWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = UnidadDetailSerializer(instance).data
        return success_response(data=payload, message="Unidad actualizada")


class AdultoUnidadRolListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = AdultoUnidadRol.objects.select_related("unidad", "adulto__persona").order_by("unidad__nombre", "rol")

    def get_queryset(self):
        return (
            AdultoUnidadRol.objects.select_related("unidad", "adulto__persona")
            .filter(unidad__in=get_accessible_unidades_qs(self.request.user))
            .order_by("unidad__nombre", "rol")
        )

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
        unidad_id = request.data.get("unidad")
        unidad = get_object_or_404(get_accessible_unidades_qs(request.user), pk=unidad_id)
        if not can_manage_group_data(request.user, unidad.grupo_id):
            raise PermissionDenied("No tiene permisos para asignar adultos en esta unidad")
        serializer = AdultoUnidadRolWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not get_accessible_adultos_qs(request.user).filter(pk=serializer.validated_data["adulto"].pk).exists():
            raise PermissionDenied("No tiene permisos para asignar este adulto")
        instance = serializer.save()
        payload = AdultoUnidadRolListSerializer(instance).data
        return success_response(data=payload, message="Asignacion creada", status_code=status.HTTP_201_CREATED)


class AdultoUnidadRolRetrieveUpdateView(GenericAPIView):
    queryset = AdultoUnidadRol.objects.select_related("unidad", "adulto__persona")

    def get_queryset(self):
        return AdultoUnidadRol.objects.select_related("unidad", "adulto__persona").filter(
            unidad__in=get_accessible_unidades_qs(self.request.user)
        )

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = AdultoUnidadRolListSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_manage_group_data(request.user, instance.unidad.grupo_id):
            raise PermissionDenied("No tiene permisos para editar esta asignacion")
        _reject_immutable_relationships(request, {"unidad", "adulto"})
        serializer = AdultoUnidadRolWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = AdultoUnidadRolListSerializer(instance).data
        return success_response(data=payload, message="Asignacion actualizada")


class SubgrupoListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Subgrupo.objects.select_related("unidad", "lider_juvenil__persona").order_by("unidad__nombre", "nombre")

    def get_queryset(self):
        return (
            Subgrupo.objects.select_related("unidad", "lider_juvenil__persona")
            .filter(unidad__in=get_accessible_unidades_qs(self.request.user))
            .order_by("unidad__nombre", "nombre")
        )

    def get(self, request):
        queryset = self.get_queryset()

        unidad_id = request.query_params.get("unidad_id")
        if unidad_id:
            queryset = queryset.filter(unidad_id=unidad_id)

        return self._list_response(queryset, SubgrupoListSerializer)

    def post(self, request):
        unidad_id = request.data.get("unidad")
        unidad = get_object_or_404(get_accessible_unidades_qs(request.user), pk=unidad_id)
        if not can_manage_group_data(request.user, unidad.grupo_id):
            raise PermissionDenied("No tiene permisos para crear subgrupos en esta unidad")
        serializer = SubgrupoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = SubgrupoListSerializer(instance).data
        return success_response(data=payload, message="Subgrupo creado", status_code=status.HTTP_201_CREATED)


class SubgrupoRetrieveUpdateView(GenericAPIView):
    queryset = Subgrupo.objects.select_related("unidad", "lider_juvenil__persona")

    def get_queryset(self):
        return Subgrupo.objects.select_related("unidad", "lider_juvenil__persona").filter(
            unidad__in=get_accessible_unidades_qs(self.request.user)
        )

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = SubgrupoListSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_manage_group_data(request.user, instance.unidad.grupo_id):
            raise PermissionDenied("No tiene permisos para editar este subgrupo")
        _reject_immutable_relationships(request, {"unidad"})
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

    def get_queryset(self):
        return (
            SubgrupoMiembro.objects.select_related("subgrupo", "beneficiario__persona")
            .filter(subgrupo__in=get_accessible_subgrupos_qs(self.request.user))
            .order_by("subgrupo__nombre", "beneficiario__persona__apellidos")
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
        subgrupo_id = request.data.get("subgrupo")
        subgrupo = get_object_or_404(get_accessible_subgrupos_qs(request.user), pk=subgrupo_id)
        editable_unidad_ids = set(get_editable_unidad_ids(request.user))
        if not can_manage_group_data(request.user, subgrupo.unidad.grupo_id) and subgrupo.unidad_id not in editable_unidad_ids:
            raise PermissionDenied("No tiene permisos para editar miembros de este subgrupo")
        serializer = SubgrupoMiembroWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = SubgrupoMiembroListSerializer(instance).data
        return success_response(data=payload, message="Miembro asignado", status_code=status.HTTP_201_CREATED)


class SubgrupoMiembroRetrieveUpdateView(GenericAPIView):
    queryset = SubgrupoMiembro.objects.select_related("subgrupo", "beneficiario__persona")

    def get_queryset(self):
        return get_accessible_subgrupo_miembros_qs(self.request.user).select_related("subgrupo", "beneficiario__persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = SubgrupoMiembroListSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        editable_unidad_ids = set(get_editable_unidad_ids(request.user))
        if not can_manage_group_data(request.user, instance.subgrupo.unidad.grupo_id) and instance.subgrupo.unidad_id not in editable_unidad_ids:
            raise PermissionDenied("No tiene permisos para editar este miembro")
        _reject_immutable_relationships(request, {"subgrupo", "beneficiario"})
        serializer = SubgrupoMiembroWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = SubgrupoMiembroListSerializer(instance).data
        return success_response(data=payload, message="Miembro actualizado")

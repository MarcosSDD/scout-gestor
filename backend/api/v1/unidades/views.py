from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView

from api.v1.access import (
    can_edit_unidad, can_manage_group_data, get_accessible_adultos_qs,
    get_accessible_beneficiarios_qs,
    get_accessible_subgrupo_miembros_qs,
    get_accessible_subgrupos_qs, get_accessible_unidades_qs, get_editable_unidad_ids,
    get_manageable_grupos_qs, is_full_access,
)
from api.v1.responses import success_response
from api.v1.unidades.serializers import (
    AdultoUnidadRolListSerializer, AdultoUnidadRolWriteSerializer, OpcionGrupoSerializer, OpcionUnidadQuerySerializer,
    OpcionUnidadSerializer,
    OpcionDestinoMembresiaSerializer, OpcionPersonaSerializer, SubgrupoListSerializer, SubgrupoMiembroListSerializer,
    SubgrupoMiembroReasignacionSerializer, SubgrupoMiembroWriteSerializer,
    SubgrupoWriteSerializer, UnidadDetailSerializer, UnidadListSerializer, UnidadWriteSerializer,
)
from personas.models import Beneficiario, EstadoPersona
from unidades.models import AdultoUnidadRol, Subgrupo, SubgrupoMiembro, Unidad
from unidades.services import (
    create_adulto_unidad_rol, create_subgrupo, create_subgrupo_miembro, create_unidad,
    reassign_subgrupo_miembro, update_adulto_unidad_rol, update_subgrupo, update_unidad,
)


class _ListResponseMixin:
    def _list_response(self, queryset, serializer_class):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return success_response(data=serializer.data, meta={key: response.data[key] for key in ("count", "next", "previous")})
        return success_response(data=serializer_class(queryset, many=True).data)


def _reject_fields(request, fields, message="Esta relacion no puede modificarse por este endpoint"):
    invalid = set(request.data) - set(fields)
    if invalid:
        raise ValidationError({field: message for field in invalid})


def _service(command, **kwargs):
    try:
        return command(**kwargs)
    except DjangoValidationError as exc:
        raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}) from exc


def _can_manage_memberships(user, unidad):
    return can_manage_group_data(user, unidad.grupo_id) or unidad.id in set(get_editable_unidad_ids(user))


def _meta(user, unidad, kind):
    group_manager = can_manage_group_data(user, unidad.grupo_id)
    membership_manager = _can_manage_memberships(user, unidad)
    if kind == "unidad":
        permissions = {
            "can_edit": group_manager,
            "can_create_subgroup": group_manager,
            "can_manage_memberships": membership_manager,
            "can_manage_adult_assignments": group_manager,
        }
    elif kind == "subgrupo":
        permissions = {
            "can_edit": group_manager,
            "can_manage_memberships": membership_manager,
            "can_assign_leader": group_manager,
        }
    elif kind == "miembro":
        permissions = {"can_reassign": membership_manager}
    else:
        permissions = {"can_edit_role": group_manager}
    return {"permissions": permissions}


class UnidadListCreateView(_ListResponseMixin, GenericAPIView):
    def get_queryset(self):
        return get_accessible_unidades_qs(self.request.user).select_related("grupo", "rama").order_by("nombre")

    def get(self, request):
        queryset = self.get_queryset()
        for field, param in (("grupo_id", "grupo_id"), ("rama_id", "rama_id"), ("estado", "estado")):
            if request.query_params.get(param):
                queryset = queryset.filter(**{field: request.query_params[param]})
        if request.query_params.get("search"):
            queryset = queryset.filter(nombre__icontains=request.query_params["search"].strip())
        return self._list_response(queryset, UnidadListSerializer)

    def post(self, request):
        grupo_id = request.data.get("grupo")
        if not grupo_id or not can_manage_group_data(request.user, int(grupo_id)):
            raise PermissionDenied("No tiene permisos para crear unidades en este grupo")
        serializer = UnidadWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = _service(create_unidad, user=request.user, data=serializer.validated_data)
        return success_response(data=UnidadDetailSerializer(instance).data, message="Unidad creada", status_code=status.HTTP_201_CREATED)


class UnidadRetrieveUpdateView(GenericAPIView):
    def get_queryset(self):
        return get_accessible_unidades_qs(self.request.user).select_related("grupo", "rama")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        return success_response(data=UnidadDetailSerializer(instance).data, meta=_meta(request.user, instance, "unidad"))

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_unidad(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar esta unidad")
        _reject_fields(request, {"nombre", "tipo_composicion", "estado", "cupo_maximo"})
        serializer = UnidadWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = _service(update_unidad, user=request.user, unidad=instance, data=serializer.validated_data)
        return success_response(data=UnidadDetailSerializer(instance).data, message="Unidad actualizada")


class AdultoUnidadRolListCreateView(_ListResponseMixin, GenericAPIView):
    def get_queryset(self):
        return AdultoUnidadRol.objects.select_related("unidad", "adulto__persona").filter(unidad__in=get_accessible_unidades_qs(self.request.user)).order_by("unidad__nombre", "rol")

    def get(self, request):
        queryset = self.get_queryset()
        if request.query_params.get("unidad_id"):
            queryset = queryset.filter(unidad_id=request.query_params["unidad_id"])
        return self._list_response(queryset, AdultoUnidadRolListSerializer)

    def post(self, request):
        serializer = AdultoUnidadRolWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        unidad = serializer.validated_data["unidad"]
        adulto = serializer.validated_data["adulto"]
        if not can_manage_group_data(request.user, unidad.grupo_id):
            raise PermissionDenied("No tiene permisos para asignar adultos en esta unidad")
        if not is_full_access(request.user) and not AdultoUnidadRol.objects.filter(adulto=adulto, unidad__grupo_id=unidad.grupo_id).exists():
            raise PermissionDenied("El adulto debe estar vinculado de forma segura al grupo.")
        instance = _service(create_adulto_unidad_rol, user=request.user, data=serializer.validated_data)
        return success_response(data=AdultoUnidadRolListSerializer(instance).data, message="Asignacion creada", status_code=status.HTTP_201_CREATED)


class AdultoUnidadRolRetrieveUpdateView(GenericAPIView):
    def get_queryset(self):
        return AdultoUnidadRol.objects.select_related("unidad", "adulto__persona").filter(unidad__in=get_accessible_unidades_qs(self.request.user))

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        return success_response(data=AdultoUnidadRolListSerializer(instance).data, meta=_meta(request.user, instance.unidad, "adulto"))

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_manage_group_data(request.user, instance.unidad.grupo_id):
            raise PermissionDenied("No tiene permisos para editar esta asignacion")
        _reject_fields(request, {"rol"})
        serializer = AdultoUnidadRolWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = _service(update_adulto_unidad_rol, user=request.user, asignacion=instance, data=serializer.validated_data)
        return success_response(data=AdultoUnidadRolListSerializer(instance).data, message="Asignacion actualizada")


class SubgrupoListCreateView(_ListResponseMixin, GenericAPIView):
    def get_queryset(self):
        return get_accessible_subgrupos_qs(self.request.user).select_related("unidad", "lider_juvenil__persona").order_by("unidad__nombre", "nombre")

    def get(self, request):
        queryset = self.get_queryset()
        if request.query_params.get("unidad_id"):
            queryset = queryset.filter(unidad_id=request.query_params["unidad_id"])
        return self._list_response(queryset, SubgrupoListSerializer)

    def post(self, request):
        serializer = SubgrupoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not can_manage_group_data(request.user, serializer.validated_data["unidad"].grupo_id):
            raise PermissionDenied("No tiene permisos para crear subgrupos en esta unidad")
        instance = _service(create_subgrupo, user=request.user, data=serializer.validated_data)
        return success_response(data=SubgrupoListSerializer(instance).data, message="Subgrupo creado", status_code=status.HTTP_201_CREATED)


class SubgrupoRetrieveUpdateView(GenericAPIView):
    def get_queryset(self):
        return get_accessible_subgrupos_qs(self.request.user).select_related("unidad", "lider_juvenil__persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        return success_response(data=SubgrupoListSerializer(instance).data, meta=_meta(request.user, instance.unidad, "subgrupo"))

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_manage_group_data(request.user, instance.unidad.grupo_id):
            raise PermissionDenied("No tiene permisos para editar este subgrupo")
        _reject_fields(request, {"nombre", "lider_juvenil"})
        serializer = SubgrupoWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = _service(update_subgrupo, user=request.user, subgrupo=instance, data=serializer.validated_data)
        return success_response(data=SubgrupoListSerializer(instance).data, message="Subgrupo actualizado")


class SubgrupoMiembroListCreateView(_ListResponseMixin, GenericAPIView):
    def get_queryset(self):
        return get_accessible_subgrupo_miembros_qs(self.request.user).select_related("subgrupo__unidad", "beneficiario__persona").order_by("subgrupo__nombre", "beneficiario__persona__apellidos")

    def get(self, request):
        queryset = self.get_queryset()
        for field in ("subgrupo_id", "beneficiario_id"):
            if request.query_params.get(field):
                queryset = queryset.filter(**{field: request.query_params[field]})
        return self._list_response(queryset, SubgrupoMiembroListSerializer)

    def post(self, request):
        serializer = SubgrupoMiembroWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not _can_manage_memberships(request.user, serializer.validated_data["subgrupo"].unidad):
            raise PermissionDenied("No tiene permisos para editar miembros de este subgrupo")
        instance = _service(create_subgrupo_miembro, user=request.user, data=serializer.validated_data)
        return success_response(data=SubgrupoMiembroListSerializer(instance).data, message="Miembro asignado", status_code=status.HTTP_201_CREATED)


class SubgrupoMiembroRetrieveUpdateView(GenericAPIView):
    def get_queryset(self):
        return get_accessible_subgrupo_miembros_qs(self.request.user).select_related("subgrupo__unidad", "beneficiario__persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        return success_response(data=SubgrupoMiembroListSerializer(instance).data, meta=_meta(request.user, instance.subgrupo.unidad, "miembro"))


class SubgrupoMiembroReasignacionView(GenericAPIView):
    def patch(self, request, pk):
        miembro = get_object_or_404(get_accessible_subgrupo_miembros_qs(request.user).select_related("subgrupo__unidad"), pk=pk)
        _reject_fields(request, {"subgrupo"}, "Este endpoint solo acepta subgrupo.")
        serializer = SubgrupoMiembroReasignacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        destino = serializer.validated_data["subgrupo"]
        if not _can_manage_memberships(request.user, miembro.subgrupo.unidad) or not _can_manage_memberships(request.user, destino.unidad):
            raise PermissionDenied("No tiene permisos sobre la unidad de origen o destino.")
        instance = _service(reassign_subgrupo_miembro, user=request.user, miembro=miembro, subgrupo=destino)
        return success_response(data=SubgrupoMiembroListSerializer(instance).data, message="Miembro reasignado")


class OpcionesGruposView(_ListResponseMixin, GenericAPIView):
    def get(self, request):
        queryset = get_manageable_grupos_qs(request.user).order_by("nombre_oficial")
        if request.query_params.get("search"):
            queryset = queryset.filter(nombre_oficial__icontains=request.query_params["search"].strip())
        return self._list_response(queryset, OpcionGrupoSerializer)


class OpcionesUnidadesView(GenericAPIView):
    def get(self, request):
        query_serializer = OpcionUnidadQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        accessible_beneficiarios = get_accessible_beneficiarios_qs(request.user)
        queryset = (
            Unidad.objects.select_related("grupo", "rama")
            .filter(
                Q(pk__in=get_accessible_unidades_qs(request.user))
                | Q(pk__in=accessible_beneficiarios.values("unidad_id")),
                rama_id=query_serializer.validated_data["rama_id"],
            )
            .distinct()
            .order_by("grupo__nombre_oficial", "nombre")
        )
        return success_response(data=OpcionUnidadSerializer(queryset, many=True).data)


class OpcionesBeneficiariosView(_ListResponseMixin, GenericAPIView):
    def get(self, request):
        subgrupo_id = request.query_params.get("subgrupo_id")
        if subgrupo_id:
            subgrupo = get_object_or_404(get_accessible_subgrupos_qs(request.user).select_related("unidad"), pk=subgrupo_id)
            if not can_manage_group_data(request.user, subgrupo.unidad.grupo_id):
                raise PermissionDenied("No tiene permisos para asignar lideres en este subgrupo")
            queryset = Beneficiario.objects.select_related("persona").filter(
                membresias_subgrupo__subgrupo=subgrupo, persona__estado=EstadoPersona.ACTIVO
            ).distinct()
        else:
            unidad = get_object_or_404(get_accessible_unidades_qs(request.user), pk=request.query_params.get("unidad_id"))
            if not _can_manage_memberships(request.user, unidad):
                raise PermissionDenied("No tiene permisos para esta unidad")
            queryset = Beneficiario.objects.select_related("persona").filter(
                unidad=unidad, persona__estado=EstadoPersona.ACTIVO
            ).exclude(membresias_subgrupo__subgrupo__unidad=unidad).distinct()
        if request.query_params.get("search"):
            search = request.query_params["search"].strip()
            queryset = queryset.filter(Q(persona__nombres__icontains=search) | Q(persona__apellidos__icontains=search))
        queryset = queryset.order_by("persona__apellidos", "persona__nombres")
        return self._list_response(queryset, OpcionPersonaSerializer)


class OpcionesAdultosView(_ListResponseMixin, GenericAPIView):
    def get(self, request):
        unidad = get_object_or_404(get_accessible_unidades_qs(request.user), pk=request.query_params.get("unidad_id"))
        if not can_manage_group_data(request.user, unidad.grupo_id):
            raise PermissionDenied("No tiene permisos para esta unidad")
        queryset = get_accessible_adultos_qs(request.user).select_related("persona").filter(persona__estado=EstadoPersona.ACTIVO)
        if not is_full_access(request.user):
            queryset = queryset.filter(asignaciones_unidad__unidad__grupo_id=unidad.grupo_id)
        queryset = queryset.exclude(asignaciones_unidad__unidad=unidad).distinct().order_by("persona__apellidos", "persona__nombres")
        if request.query_params.get("search"):
            search = request.query_params["search"].strip()
            queryset = queryset.filter(Q(persona__nombres__icontains=search) | Q(persona__apellidos__icontains=search))
        return self._list_response(queryset, OpcionPersonaSerializer)


class OpcionesDestinosMembresiaView(_ListResponseMixin, GenericAPIView):
    def get(self, request):
        miembro = get_object_or_404(get_accessible_subgrupo_miembros_qs(request.user).select_related("subgrupo__unidad"), pk=request.query_params.get("miembro_id"))
        if not _can_manage_memberships(request.user, miembro.subgrupo.unidad):
            raise PermissionDenied("No tiene permisos para esta membresia")
        if is_full_access(request.user):
            allowed = Q()
        else:
            allowed = Q(unidad__grupo_id__in=get_manageable_grupos_qs(request.user).values("id")) | Q(
                unidad_id__in=get_editable_unidad_ids(request.user)
            )
        queryset = Subgrupo.objects.select_related("unidad").filter(allowed, unidad__estado="ACTIVA")
        if request.query_params.get("search"):
            search = request.query_params["search"].strip()
            queryset = queryset.filter(Q(nombre__icontains=search) | Q(unidad__nombre__icontains=search))
        queryset = queryset.order_by("unidad__nombre", "nombre")
        return self._list_response(queryset, OpcionDestinoMembresiaSerializer)

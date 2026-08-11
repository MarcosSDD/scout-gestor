from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from api.v1.personas.serializers import (
    AdultoDetailSerializer,
    AdultoCertificadoRenewalSerializer,
    AdultoListSerializer,
    AdultoWriteSerializer,
    ApoderadoBeneficiarioListSerializer,
    ApoderadoBeneficiarioWriteSerializer,
    ApoderadoDetailSerializer,
    ApoderadoListSerializer,
    ApoderadoWriteSerializer,
    AreaDesarrolloSerializer,
    BeneficiarioDetailSerializer,
    BeneficiarioAsignacionSerializer,
    BeneficiarioListSerializer,
    BeneficiarioWriteSerializer,
    PersonaDetailSerializer,
    PersonaListSerializer,
    PersonaWriteSerializer,
    RegistroProgresionScoutListSerializer,
    RegistroProgresionScoutWriteSerializer,
    ValidarRutSerializer,
)
from api.v1.access import (
    can_download_adulto_certificate,
    can_renew_adulto_certificate,
    can_reassign_beneficiario,
    can_edit_adulto,
    can_edit_apoderado,
    can_edit_apoderado_committee,
    can_edit_beneficiario,
    can_edit_persona,
    can_edit_persona_identity,
    can_edit_progresion,
    can_manage_group_data,
    can_view_persona_photo,
    get_accessible_adultos_qs,
    get_accessible_apoderados_qs,
    get_accessible_beneficiarios_qs,
    get_accessible_personas_qs,
    get_accessible_progresiones_qs,
    get_adulto_detail_permissions,
    get_apoderado_detail_permissions,
    get_beneficiario_detail_permissions,
    get_persona_detail_permissions,
)
from api.v1.responses import success_response
from api.v1.personas.services import create_beneficiario, reassign_beneficiario, renew_adulto_certificate
from personas.models import (
    Adulto,
    Apoderado,
    ApoderadoBeneficiario,
    AreaDesarrollo,
    Beneficiario,
    Persona,
    RegistroProgresionScout,
)


class _FileWriteThrottleMixin:
    throttle_scope = "file_upload"

    def get_throttles(self):
        if self.request.method in {"POST", "PATCH", "PUT"}:
            return [ScopedRateThrottle()]
        return super().get_throttles()


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


def _integer_query_param(request, name):
    value = request.query_params.get(name)
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({name: "Debe ser un entero valido"}) from exc


def _boolean_query_param(request, name):
    value = request.query_params.get(name)
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "si"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValidationError({name: "Debe ser true o false"})


def _filter_person_search(queryset, search, prefix="persona__"):
    if not search:
        return queryset
    search = search.strip()
    return queryset.filter(
        Q(**{f"{prefix}nombres__icontains": search})
        | Q(**{f"{prefix}apellidos__icontains": search})
    )


def _detail(serializer_class, instance, request):
    return serializer_class(instance, context={"request": request}).data


def _reject_immutable_relationships(request, fields):
    prohibited = set(request.data) & set(fields)
    if prohibited:
        raise ValidationError({field: "Esta relacion no puede modificarse por este endpoint" for field in prohibited})


def _reject_persona_fields_for_own_guardian(request):
    permitted = {"direccion", "telefono", "email", "foto"}
    prohibited = set(request.data) - permitted
    if prohibited:
        raise ValidationError({field: "Los apoderados solo pueden modificar sus datos de contacto y foto" for field in prohibited})


def _reject_unexpected_fields(request, allowed_fields):
    unexpected = set(request.data) - set(allowed_fields)
    if unexpected:
        raise ValidationError({field: "Este campo no puede modificarse por este endpoint" for field in unexpected})


def _private_file_response(field_file, *, attachment=False):
    response = FileResponse(field_file.open("rb"), as_attachment=attachment, filename=field_file.name.rsplit("/", 1)[-1])
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


class PersonaListCreateView(_FileWriteThrottleMixin, _ListResponseMixin, GenericAPIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = get_accessible_personas_qs(self.request.user).order_by("apellidos", "nombres")

        estado = self.request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(estado=estado)

        search = self.request.query_params.get("search")
        if search:
            search = search.strip()
            queryset = queryset.filter(Q(nombres__icontains=search) | Q(apellidos__icontains=search))

        return queryset

    def get(self, request):
        return self._list_response(self.get_queryset(), PersonaListSerializer)

    def post(self, request):
        grupo_id = request.data.get("grupo_id")
        if not (request.user.is_staff or request.user.is_superuser):
            if not grupo_id or not can_manage_group_data(request.user, int(grupo_id)):
                raise PermissionDenied("No tiene permisos para crear personas")
        serializer = PersonaWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = _detail(PersonaDetailSerializer, instance, request)
        return success_response(data=payload, message="Persona creada", status_code=status.HTTP_201_CREATED)


class PersonaRetrieveUpdateView(_FileWriteThrottleMixin, GenericAPIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = Persona.objects.order_by("apellidos", "nombres")

    def get_queryset(self):
        return get_accessible_personas_qs(self.request.user).order_by("apellidos", "nombres")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = PersonaDetailSerializer(instance, context={"request": request})
        return success_response(data=serializer.data, meta={"permissions": get_persona_detail_permissions(request.user, instance)})

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_persona(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar esta persona")
        if not can_edit_persona_identity(request.user, instance):
            _reject_persona_fields_for_own_guardian(request)
        serializer = PersonaWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = _detail(PersonaDetailSerializer, instance, request)
        return success_response(data=payload, message="Persona actualizada")


class ValidarRutView(APIView):
    def post(self, request):
        serializer = ValidarRutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = {
            "rut": serializer.validated_data["rut"],
            "valido": True,
        }
        return success_response(data=payload, message="RUT valido")


class AdultoListCreateView(_FileWriteThrottleMixin, _ListResponseMixin, GenericAPIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = Adulto.objects.select_related("persona").order_by("persona__apellidos", "persona__nombres")

    def get_queryset(self):
        queryset = get_accessible_adultos_qs(self.request.user).select_related("persona").order_by(
            "persona__apellidos", "persona__nombres"
        )

        queryset = _filter_person_search(queryset, self.request.query_params.get("search"))
        estado = self.request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(persona__estado=estado)
        rol_principal = self.request.query_params.get("rol_principal")
        if rol_principal:
            queryset = queryset.filter(rol_principal=rol_principal)
        certificado_vigente = _boolean_query_param(self.request, "certificado_vigente")
        if certificado_vigente is not None:
            comparison = "certificado_vigencia_hasta__gte" if certificado_vigente else "certificado_vigencia_hasta__lt"
            queryset = queryset.filter(**{comparison: timezone.localdate()})
        unidad_id = _integer_query_param(self.request, "unidad_id")
        if unidad_id:
            queryset = queryset.filter(asignaciones_unidad__unidad_id=unidad_id)
        grupo_id = _integer_query_param(self.request, "grupo_id")
        if grupo_id:
            queryset = queryset.filter(asignaciones_unidad__unidad__grupo_id=grupo_id)
        return queryset.distinct()

    def get(self, request):
        return self._list_response(self.get_queryset(), AdultoListSerializer)

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para crear adultos")
        serializer = AdultoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = _detail(AdultoDetailSerializer, instance, request)
        return success_response(data=payload, message="Adulto creado", status_code=status.HTTP_201_CREATED)


class AdultoRetrieveUpdateView(_FileWriteThrottleMixin, GenericAPIView):
    queryset = Adulto.objects.select_related("persona")

    def get_queryset(self):
        return get_accessible_adultos_qs(self.request.user).select_related("persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = AdultoDetailSerializer(instance, context={"request": request})
        return success_response(data=serializer.data, meta={"permissions": get_adulto_detail_permissions(request.user, instance)})

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_adulto(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar adultos")
        _reject_immutable_relationships(request, {"persona"})
        serializer = AdultoWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = _detail(AdultoDetailSerializer, instance, request)
        return success_response(data=payload, message="Adulto actualizado")


class BeneficiarioListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Beneficiario.objects.select_related("persona", "rama_actual", "unidad").order_by(
        "persona__apellidos",
        "persona__nombres",
    )

    def get_queryset(self):
        return get_accessible_beneficiarios_qs(self.request.user).select_related("persona", "rama_actual", "unidad__grupo").order_by(
            "persona__apellidos",
            "persona__nombres",
        )

    def get(self, request):
        queryset = self.get_queryset()

        unidad_id = _integer_query_param(request, "unidad_id")
        if unidad_id:
            queryset = queryset.filter(unidad_id=unidad_id)

        rama_id = _integer_query_param(request, "rama_id")
        if rama_id:
            queryset = queryset.filter(rama_actual_id=rama_id)

        grupo_id = _integer_query_param(request, "grupo_id")
        if grupo_id:
            queryset = queryset.filter(unidad__grupo_id=grupo_id)

        estado = request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(persona__estado=estado)

        queryset = _filter_person_search(queryset, request.query_params.get("search"))

        return self._list_response(queryset, BeneficiarioListSerializer)

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para crear beneficiarios")
        serializer = BeneficiarioWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = create_beneficiario(user=request.user, data=serializer.validated_data)
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            raise ValidationError(details) from exc
        payload = _detail(BeneficiarioDetailSerializer, instance, request)
        return success_response(data=payload, message="Beneficiario creado", status_code=status.HTTP_201_CREATED)


class BeneficiarioRetrieveUpdateView(GenericAPIView):
    queryset = Beneficiario.objects.select_related("persona", "rama_actual", "unidad").prefetch_related(
        "registros_progresion__areas"
    )

    def get_queryset(self):
        return get_accessible_beneficiarios_qs(self.request.user).select_related(
            "persona", "rama_actual", "unidad__grupo"
        ).prefetch_related("registros_progresion__areas")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = BeneficiarioDetailSerializer(instance, context={"request": request})
        return success_response(data=serializer.data, meta={"permissions": get_beneficiario_detail_permissions(request.user, instance)})

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_beneficiario(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar este beneficiario")
        _reject_immutable_relationships(request, {"persona", "rama_actual", "unidad"})
        serializer = BeneficiarioWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = _detail(BeneficiarioDetailSerializer, instance, request)
        return success_response(data=payload, message="Beneficiario actualizado")


class BeneficiarioAsignacionView(GenericAPIView):
    queryset = Beneficiario.objects.select_related("persona", "unidad__grupo")

    def patch(self, request, pk):
        beneficiario = get_object_or_404(self.queryset, pk=pk)
        _reject_unexpected_fields(request, {"rama_actual", "unidad"})
        serializer = BeneficiarioAsignacionSerializer(beneficiario, data=request.data)
        serializer.is_valid(raise_exception=True)
        destination = serializer.validated_data["unidad"]
        if not can_reassign_beneficiario(request.user, beneficiario, destination):
            raise PermissionDenied("No tiene permisos para reasignar este beneficiario")
        try:
            beneficiario = reassign_beneficiario(user=request.user, beneficiario=beneficiario, data=serializer.validated_data)
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            raise ValidationError(details) from exc
        payload = _detail(BeneficiarioDetailSerializer, beneficiario, request)
        return success_response(data=payload, message="Asignacion de beneficiario actualizada")


class AreaDesarrolloListView(_ListResponseMixin, GenericAPIView):
    queryset = AreaDesarrollo.objects.order_by("nombre")

    def get(self, request):
        return self._list_response(self.get_queryset(), AreaDesarrolloSerializer)


class RegistroProgresionScoutListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = RegistroProgresionScout.objects.select_related("beneficiario__persona").prefetch_related("areas")

    def get_queryset(self):
        return get_accessible_progresiones_qs(self.request.user).select_related("beneficiario__persona").prefetch_related("areas")

    def get(self, request):
        queryset = self.get_queryset()

        beneficiario_id = request.query_params.get("beneficiario_id")
        if beneficiario_id:
            queryset = queryset.filter(beneficiario_id=beneficiario_id)

        area_id = request.query_params.get("area_id")
        if area_id:
            queryset = queryset.filter(areas__id=area_id)

        tipo = request.query_params.get("tipo")
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        fecha_desde = request.query_params.get("fecha_desde")
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)

        fecha_hasta = request.query_params.get("fecha_hasta")
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        return self._list_response(queryset.distinct(), RegistroProgresionScoutListSerializer)

    def post(self, request):
        serializer = RegistroProgresionScoutWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        beneficiario = serializer.validated_data["beneficiario"]
        if not can_edit_beneficiario(request.user, beneficiario):
            raise PermissionDenied("No tiene permisos para crear progresiones para este beneficiario")
        instance = serializer.save()
        payload = RegistroProgresionScoutListSerializer(instance, context={"request": request}).data
        return success_response(data=payload, message="Registro de progresion creado", status_code=status.HTTP_201_CREATED)


class RegistroProgresionScoutRetrieveUpdateView(GenericAPIView):
    queryset = RegistroProgresionScout.objects.select_related("beneficiario__persona").prefetch_related("areas")

    def get_queryset(self):
        return get_accessible_progresiones_qs(self.request.user).select_related("beneficiario__persona").prefetch_related("areas")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = RegistroProgresionScoutListSerializer(instance, context={"request": request})
        return success_response(data=serializer.data, meta={"permissions": {"can_edit": can_edit_progresion(request.user, instance)}})

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_progresion(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar esta progresion")
        _reject_immutable_relationships(request, {"beneficiario"})
        serializer = RegistroProgresionScoutWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = RegistroProgresionScoutListSerializer(instance, context={"request": request}).data
        return success_response(data=payload, message="Registro de progresion actualizado")


class ApoderadoListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Apoderado.objects.select_related("persona").order_by("persona__apellidos", "persona__nombres")

    def get_queryset(self):
        queryset = get_accessible_apoderados_qs(self.request.user).select_related("persona").order_by(
            "persona__apellidos", "persona__nombres"
        )

        queryset = _filter_person_search(queryset, self.request.query_params.get("search"))
        estado = self.request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(persona__estado=estado)
        es_miembro_comite = _boolean_query_param(self.request, "es_miembro_comite")
        if es_miembro_comite is not None:
            queryset = queryset.filter(es_miembro_comite=es_miembro_comite)
        beneficiario_id = _integer_query_param(self.request, "beneficiario_id")
        if beneficiario_id:
            queryset = queryset.filter(relaciones_beneficiarios__beneficiario_id=beneficiario_id)
        unidad_id = _integer_query_param(self.request, "unidad_id")
        if unidad_id:
            queryset = queryset.filter(relaciones_beneficiarios__beneficiario__unidad_id=unidad_id)
        grupo_id = _integer_query_param(self.request, "grupo_id")
        if grupo_id:
            queryset = queryset.filter(relaciones_beneficiarios__beneficiario__unidad__grupo_id=grupo_id)
        return queryset.distinct()

    def get(self, request):
        return self._list_response(self.get_queryset(), ApoderadoListSerializer)

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para crear apoderados")
        serializer = ApoderadoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = _detail(ApoderadoDetailSerializer, instance, request)
        return success_response(data=payload, message="Apoderado creado", status_code=status.HTTP_201_CREATED)


class ApoderadoRetrieveUpdateView(GenericAPIView):
    queryset = Apoderado.objects.select_related("persona")

    def get_queryset(self):
        return get_accessible_apoderados_qs(self.request.user).select_related("persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = ApoderadoDetailSerializer(instance, context={"request": request})
        return success_response(data=serializer.data, meta={"permissions": get_apoderado_detail_permissions(request.user, instance)})

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_apoderado(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar este apoderado")
        _reject_immutable_relationships(request, {"persona"})
        if not can_edit_apoderado_committee(request.user, instance) and ({"es_miembro_comite", "rol_comite"} & set(request.data)):
            raise PermissionDenied("No tiene permisos para editar datos de comite")
        serializer = ApoderadoWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = _detail(ApoderadoDetailSerializer, instance, request)
        return success_response(data=payload, message="Apoderado actualizado")


class ApoderadoBeneficiarioListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = ApoderadoBeneficiario.objects.select_related("apoderado__persona", "beneficiario__persona").order_by(
        "beneficiario__persona__apellidos",
        "beneficiario__persona__nombres",
    )

    def get_queryset(self):
        return (
            ApoderadoBeneficiario.objects.select_related("apoderado__persona", "beneficiario__persona")
            .filter(beneficiario__in=get_accessible_beneficiarios_qs(self.request.user))
            .order_by("beneficiario__persona__apellidos", "beneficiario__persona__nombres")
        )

    def get(self, request):
        queryset = self.get_queryset()

        beneficiario_id = request.query_params.get("beneficiario_id")
        if beneficiario_id:
            queryset = queryset.filter(beneficiario_id=beneficiario_id)

        apoderado_id = request.query_params.get("apoderado_id")
        if apoderado_id:
            queryset = queryset.filter(apoderado_id=apoderado_id)

        return self._list_response(queryset, ApoderadoBeneficiarioListSerializer)

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para crear relaciones apoderado-beneficiario")
        serializer = ApoderadoBeneficiarioWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = ApoderadoBeneficiarioListSerializer(instance).data
        return success_response(data=payload, message="Relacion creada", status_code=status.HTTP_201_CREATED)


class ApoderadoBeneficiarioRetrieveUpdateView(GenericAPIView):
    queryset = ApoderadoBeneficiario.objects.select_related("apoderado__persona", "beneficiario__persona")

    def get_queryset(self):
        return ApoderadoBeneficiario.objects.select_related("apoderado__persona", "beneficiario__persona").filter(
            beneficiario__in=get_accessible_beneficiarios_qs(self.request.user)
        )

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = ApoderadoBeneficiarioListSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para editar esta relacion")
        _reject_immutable_relationships(request, {"apoderado", "beneficiario"})
        serializer = ApoderadoBeneficiarioWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = ApoderadoBeneficiarioListSerializer(instance).data
        return success_response(data=payload, message="Relacion actualizada")


class PersonaFotoDownloadView(APIView):
    def get(self, request, pk):
        persona = get_object_or_404(Persona.objects.all(), pk=pk)
        if not can_view_persona_photo(request.user, persona):
            raise PermissionDenied("No tiene permisos para descargar esta foto")
        if not persona.foto:
            raise ValidationError({"foto": "La persona no tiene una foto disponible"})
        return _private_file_response(persona.foto)


class AdultoCertificadoDownloadView(_FileWriteThrottleMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk):
        adulto = get_object_or_404(Adulto.objects.select_related("persona"), pk=pk)
        if not can_download_adulto_certificate(request.user, adulto):
            raise PermissionDenied("No tiene permisos para descargar este certificado")
        if not adulto.certificado_inhabilidades:
            raise ValidationError({"certificado_inhabilidades": "El adulto no tiene un certificado disponible"})
        return _private_file_response(adulto.certificado_inhabilidades, attachment=True)

    def patch(self, request, pk):
        adulto = get_object_or_404(Adulto.objects.select_related("persona"), pk=pk)
        if not can_renew_adulto_certificate(request.user, adulto):
            raise PermissionDenied("No tiene permisos para renovar este certificado")
        _reject_unexpected_fields(request, {"certificado_inhabilidades", "certificado_vigencia_hasta"})
        serializer = AdultoCertificadoRenewalSerializer(adulto, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            adulto = renew_adulto_certificate(user=request.user, adulto=adulto, data=serializer.validated_data)
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            raise ValidationError(details) from exc
        payload = _detail(AdultoDetailSerializer, adulto, request)
        return success_response(data=payload, message="Certificado actualizado")

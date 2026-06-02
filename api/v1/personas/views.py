from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from api.v1.personas.serializers import (
    AdultoDetailSerializer,
    AdultoListSerializer,
    AdultoWriteSerializer,
    ApoderadoBeneficiarioListSerializer,
    ApoderadoBeneficiarioWriteSerializer,
    ApoderadoDetailSerializer,
    ApoderadoListSerializer,
    ApoderadoWriteSerializer,
    AreaDesarrolloSerializer,
    BeneficiarioDetailSerializer,
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
    can_edit_beneficiario,
    can_edit_persona,
    can_edit_progresion,
    can_manage_group_data,
    get_accessible_adultos_qs,
    get_accessible_apoderados_qs,
    get_accessible_beneficiarios_qs,
    get_accessible_personas_qs,
    get_accessible_progresiones_qs,
)
from api.v1.responses import success_response
from personas.models import Adulto, Apoderado, ApoderadoBeneficiario, AreaDesarrollo, Beneficiario, Persona, RegistroProgresionScout


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


class PersonaListCreateView(_ListResponseMixin, GenericAPIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = get_accessible_personas_qs(self.request.user).order_by("apellidos", "nombres")

        estado = self.request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(estado=estado)

        search = self.request.query_params.get("search")
        if search:
            search = search.strip()
            queryset = queryset.filter(
                Q(nombres__icontains=search) | Q(apellidos__icontains=search) | Q(rut__icontains=search)
            )

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
        payload = PersonaDetailSerializer(instance).data
        return success_response(data=payload, message="Persona creada", status_code=status.HTTP_201_CREATED)


class PersonaRetrieveUpdateView(GenericAPIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = Persona.objects.order_by("apellidos", "nombres")

    def get_queryset(self):
        return get_accessible_personas_qs(self.request.user).order_by("apellidos", "nombres")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = PersonaDetailSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_persona(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar esta persona")
        serializer = PersonaWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = PersonaDetailSerializer(instance).data
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


class AdultoListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Adulto.objects.select_related("persona").order_by("persona__apellidos", "persona__nombres")

    def get_queryset(self):
        return get_accessible_adultos_qs(self.request.user).select_related("persona").order_by(
            "persona__apellidos", "persona__nombres"
        )

    def get(self, request):
        return self._list_response(self.get_queryset(), AdultoListSerializer)

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para crear adultos")
        serializer = AdultoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = AdultoDetailSerializer(instance).data
        return success_response(data=payload, message="Adulto creado", status_code=status.HTTP_201_CREATED)


class AdultoRetrieveUpdateView(GenericAPIView):
    queryset = Adulto.objects.select_related("persona")

    def get_queryset(self):
        return get_accessible_adultos_qs(self.request.user).select_related("persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = AdultoDetailSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para editar adultos")
        serializer = AdultoWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = AdultoDetailSerializer(instance).data
        return success_response(data=payload, message="Adulto actualizado")


class BeneficiarioListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Beneficiario.objects.select_related("persona", "rama_actual", "unidad").order_by(
        "persona__apellidos",
        "persona__nombres",
    )

    def get_queryset(self):
        return get_accessible_beneficiarios_qs(self.request.user).select_related("persona", "rama_actual", "unidad").order_by(
            "persona__apellidos",
            "persona__nombres",
        )

    def get(self, request):
        queryset = self.get_queryset()

        unidad_id = request.query_params.get("unidad_id")
        if unidad_id:
            queryset = queryset.filter(unidad_id=unidad_id)

        rama_id = request.query_params.get("rama_id")
        if rama_id:
            queryset = queryset.filter(rama_actual_id=rama_id)

        return self._list_response(queryset, BeneficiarioListSerializer)

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para crear beneficiarios")
        serializer = BeneficiarioWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = BeneficiarioDetailSerializer(instance).data
        return success_response(data=payload, message="Beneficiario creado", status_code=status.HTTP_201_CREATED)


class BeneficiarioRetrieveUpdateView(GenericAPIView):
    queryset = Beneficiario.objects.select_related("persona", "rama_actual", "unidad").prefetch_related(
        "registros_progresion__areas"
    )

    def get_queryset(self):
        return get_accessible_beneficiarios_qs(self.request.user).select_related(
            "persona", "rama_actual", "unidad"
        ).prefetch_related("registros_progresion__areas")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = BeneficiarioDetailSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_beneficiario(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar este beneficiario")
        serializer = BeneficiarioWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = BeneficiarioDetailSerializer(instance).data
        return success_response(data=payload, message="Beneficiario actualizado")


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
        payload = RegistroProgresionScoutListSerializer(instance).data
        return success_response(data=payload, message="Registro de progresion creado", status_code=status.HTTP_201_CREATED)


class RegistroProgresionScoutRetrieveUpdateView(GenericAPIView):
    queryset = RegistroProgresionScout.objects.select_related("beneficiario__persona").prefetch_related("areas")

    def get_queryset(self):
        return get_accessible_progresiones_qs(self.request.user).select_related("beneficiario__persona").prefetch_related("areas")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = RegistroProgresionScoutListSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_edit_progresion(request.user, instance):
            raise PermissionDenied("No tiene permisos para editar esta progresion")
        serializer = RegistroProgresionScoutWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = RegistroProgresionScoutListSerializer(instance).data
        return success_response(data=payload, message="Registro de progresion actualizado")


class ApoderadoListCreateView(_ListResponseMixin, GenericAPIView):
    queryset = Apoderado.objects.select_related("persona").order_by("persona__apellidos", "persona__nombres")

    def get_queryset(self):
        return get_accessible_apoderados_qs(self.request.user).select_related("persona").order_by(
            "persona__apellidos", "persona__nombres"
        )

    def get(self, request):
        return self._list_response(self.get_queryset(), ApoderadoListSerializer)

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para crear apoderados")
        serializer = ApoderadoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = ApoderadoDetailSerializer(instance).data
        return success_response(data=payload, message="Apoderado creado", status_code=status.HTTP_201_CREATED)


class ApoderadoRetrieveUpdateView(GenericAPIView):
    queryset = Apoderado.objects.select_related("persona")

    def get_queryset(self):
        return get_accessible_apoderados_qs(self.request.user).select_related("persona")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = ApoderadoDetailSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        own_apoderado = (
            hasattr(request.user, "persona")
            and hasattr(request.user.persona, "apoderado")
            and request.user.persona.apoderado.id == instance.id
        )
        if not (request.user.is_staff or request.user.is_superuser or own_apoderado):
            raise PermissionDenied("No tiene permisos para editar este apoderado")
        serializer = ApoderadoWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = ApoderadoDetailSerializer(instance).data
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
        serializer = ApoderadoBeneficiarioWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = ApoderadoBeneficiarioListSerializer(instance).data
        return success_response(data=payload, message="Relacion actualizada")

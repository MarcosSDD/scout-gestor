from collections import defaultdict

from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView

from api.v1.access import can_manage_group_data, get_accessible_grupos_qs
from api.v1.organizacion.serializers import (
    GrupoScoutDetailSerializer,
    GrupoScoutListSerializer,
    GrupoScoutWriteSerializer,
)
from api.v1.responses import success_response
from organizacion.models import GrupoScout
from personas.models import Beneficiario, EstadoPersona
from unidades.models import AdultoUnidadRol, EstadoUnidad, Subgrupo, SubgrupoMiembro, Unidad


class GrupoScoutListCreateView(GenericAPIView):
    def get_queryset(self):
        queryset = get_accessible_grupos_qs(self.request.user).select_related("zona", "distrito").annotate(
            total_beneficiarios_activos=Count(
                "unidades__beneficiarios",
                filter=Q(unidades__beneficiarios__persona__estado=EstadoPersona.ACTIVO),
                distinct=True,
            ),
            total_adultos_activos=Count(
                "unidades__equipo_adulto__adulto",
                filter=Q(unidades__equipo_adulto__adulto__persona__estado=EstadoPersona.ACTIVO),
                distinct=True,
            ),
        )

        zona_id = self.request.query_params.get("zona_id")
        if zona_id:
            queryset = queryset.filter(zona_id=zona_id)

        distrito_id = self.request.query_params.get("distrito_id")
        if distrito_id:
            queryset = queryset.filter(distrito_id=distrito_id)

        estado_vigencia = self.request.query_params.get("estado_vigencia")
        if estado_vigencia:
            queryset = queryset.filter(estado_vigencia=estado_vigencia)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(nombre_oficial__icontains=search.strip())

        return queryset.order_by("nombre_oficial")

    def get(self, request):
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = GrupoScoutListSerializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            meta = {
                "count": paginated_response.data["count"],
                "next": paginated_response.data["next"],
                "previous": paginated_response.data["previous"],
            }
            return success_response(data=serializer.data, meta=meta)

        serializer = GrupoScoutListSerializer(queryset, many=True)
        return success_response(data=serializer.data)

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("No tiene permisos para crear grupos")
        serializer = GrupoScoutWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = GrupoScoutDetailSerializer(instance).data
        return success_response(data=payload, message="Grupo creado", status_code=status.HTTP_201_CREATED)


class GrupoScoutRetrieveUpdateView(GenericAPIView):
    queryset = GrupoScout.objects.select_related("zona", "distrito")

    def get_queryset(self):
        return get_accessible_grupos_qs(self.request.user).select_related("zona", "distrito")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = GrupoScoutDetailSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        if not can_manage_group_data(request.user, instance.id):
            raise PermissionDenied("No tiene permisos para editar este grupo")
        serializer = GrupoScoutWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = GrupoScoutDetailSerializer(instance).data
        return success_response(data=payload, message="Grupo actualizado")


class GrupoScoutCalcularMinimoView(APIView):
    def post(self, request, pk):
        instance = get_object_or_404(get_accessible_grupos_qs(request.user), pk=pk)
        if not can_manage_group_data(request.user, instance.id):
            raise PermissionDenied("No tiene permisos para recalcular este grupo")
        minimo = instance.recalcular_minimo_miembros(save=True)
        payload = {
            "id": instance.id,
            "minimo_miembros_calculado": minimo,
            "estado_vigencia": instance.estado_vigencia,
        }
        return success_response(data=payload, message="Minimo recalculado")


def _calcular_edad(fecha_nacimiento):
    hoy = timezone.localdate()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad


class GrupoScoutEstructuraView(APIView):
    def _get_grupo(self, pk):
        unidades_qs = (
            Unidad.objects.select_related("rama")
            .prefetch_related(
                Prefetch(
                    "beneficiarios",
                    queryset=Beneficiario.objects.select_related("persona"),
                ),
                Prefetch(
                    "equipo_adulto",
                    queryset=AdultoUnidadRol.objects.select_related("adulto__persona"),
                ),
                Prefetch(
                    "subgrupos",
                    queryset=Subgrupo.objects.select_related("lider_juvenil__persona").prefetch_related(
                        Prefetch("miembros", queryset=SubgrupoMiembro.objects.select_related("beneficiario__persona"))
                    ),
                ),
            )
            .order_by("rama__edad_minima", "rama__nombre", "nombre")
        )

        return get_object_or_404(
            get_accessible_grupos_qs(self.request.user).select_related("zona", "distrito").prefetch_related(
                Prefetch("unidades", queryset=unidades_qs),
            ),
            pk=pk,
        )

    def get(self, request, pk):
        grupo = self._get_grupo(pk)

        ramas = defaultdict(
            lambda: {
                "id": None,
                "nombre": "",
                "edad_minima": None,
                "edad_maxima": None,
                "composicion_permitida": "",
                "unidades": [],
            }
        )
        total_subgrupos = 0
        total_beneficiarios = 0
        total_adultos = 0
        total_alertas_etarias = 0

        for unidad in grupo.unidades.all():
            rama = unidad.rama
            rama_bucket = ramas[rama.id]
            if rama_bucket["id"] is None:
                rama_bucket.update(
                    {
                        "id": rama.id,
                        "nombre": rama.nombre,
                        "edad_minima": rama.edad_minima,
                        "edad_maxima": rama.edad_maxima,
                        "composicion_permitida": rama.composicion_permitida,
                    }
                )

            beneficiarios_payload = []
            for beneficiario in unidad.beneficiarios.all():
                edad = _calcular_edad(beneficiario.persona.fecha_nacimiento)
                alertas = []
                if edad < rama.edad_minima or edad > rama.edad_maxima:
                    total_alertas_etarias += 1
                    alertas.append(
                        {
                            "code": "EDAD_FUERA_DE_RANGO",
                            "message": "Beneficiario fuera del rango etario de la rama",
                        }
                    )

                beneficiarios_payload.append(
                    {
                        "id": beneficiario.id,
                        "persona_id": beneficiario.persona_id,
                        "rut": beneficiario.persona.rut,
                        "nombres": beneficiario.persona.nombres,
                        "apellidos": beneficiario.persona.apellidos,
                        "sexo": beneficiario.persona.sexo,
                        "estado": beneficiario.persona.estado,
                        "edad": edad,
                        "alertas": alertas,
                    }
                )

            adultos_payload = []
            for asignacion in unidad.equipo_adulto.all():
                adultos_payload.append(
                    {
                        "id": asignacion.id,
                        "adulto_id": asignacion.adulto_id,
                        "rol": asignacion.rol,
                        "persona": {
                            "id": asignacion.adulto.persona_id,
                            "rut": asignacion.adulto.persona.rut,
                            "nombres": asignacion.adulto.persona.nombres,
                            "apellidos": asignacion.adulto.persona.apellidos,
                            "sexo": asignacion.adulto.persona.sexo,
                            "estado": asignacion.adulto.persona.estado,
                        },
                    }
                )

            subgrupos_payload = []
            for subgrupo in unidad.subgrupos.all():
                miembros = [
                    {
                        "id": miembro.id,
                        "beneficiario_id": miembro.beneficiario_id,
                        "beneficiario_nombre": f"{miembro.beneficiario.persona.nombres} {miembro.beneficiario.persona.apellidos}",
                    }
                    for miembro in subgrupo.miembros.all()
                ]
                subgrupos_payload.append(
                    {
                        "id": subgrupo.id,
                        "nombre": subgrupo.nombre,
                        "lider_juvenil_id": subgrupo.lider_juvenil_id,
                        "miembros": miembros,
                    }
                )

            total_beneficiarios += len(beneficiarios_payload)
            total_adultos += len(adultos_payload)
            total_subgrupos += len(subgrupos_payload)

            rama_bucket["unidades"].append(
                {
                    "id": unidad.id,
                    "nombre": unidad.nombre,
                    "estado": unidad.estado,
                    "tipo_composicion": unidad.composicion_actual(),
                    "es_activa": unidad.estado == EstadoUnidad.ACTIVA,
                    "beneficiarios": beneficiarios_payload,
                    "equipo_adulto": adultos_payload,
                    "subgrupos": subgrupos_payload,
                }
            )

        payload = {
            "id": grupo.id,
            "nombre_oficial": grupo.nombre_oficial,
            "zona": {"id": grupo.zona_id, "nombre": grupo.zona.nombre},
            "distrito": {"id": grupo.distrito_id, "nombre": grupo.distrito.nombre},
            "resumen": {
                "total_ramas": len(ramas),
                "total_unidades": len(grupo.unidades.all()),
                "total_subgrupos": total_subgrupos,
                "total_beneficiarios": total_beneficiarios,
                "total_adultos": total_adultos,
                "total_alertas_etarias": total_alertas_etarias,
            },
            "ramas": sorted(ramas.values(), key=lambda rama_item: (rama_item["edad_minima"], rama_item["nombre"])),
        }

        return success_response(data=payload, message="Estructura del grupo")

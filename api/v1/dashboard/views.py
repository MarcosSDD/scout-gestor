from datetime import date

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from api.v1.access import can_view_dashboard_group
from api.v1.responses import success_response
from organizacion.models import GrupoScout
from personas.models import Adulto, Beneficiario, EstadoPersona


def _porcentaje(numerador: int, denominador: int) -> float:
    if denominador == 0:
        return 0.0
    return round((numerador / denominador) * 100, 2)


def _proximo_cumpleanos(fecha_nacimiento: date, hoy: date) -> date:
    cumple = date(hoy.year, fecha_nacimiento.month, fecha_nacimiento.day)
    if cumple < hoy:
        return date(hoy.year + 1, fecha_nacimiento.month, fecha_nacimiento.day)
    return cumple


def _edad_en_fecha(fecha_nacimiento: date, fecha: date) -> int:
    edad = fecha.year - fecha_nacimiento.year
    if (fecha.month, fecha.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad


class GrupoDashboardView(APIView):
    def get(self, request, pk):
        if not can_view_dashboard_group(request.user, pk):
            raise PermissionDenied("No tiene permisos para ver el dashboard de este grupo")
        grupo = get_object_or_404(GrupoScout.objects.select_related("zona", "distrito"), pk=pk)
        hoy = timezone.localdate()

        beneficiarios_qs = Beneficiario.objects.select_related("persona", "unidad").filter(
            persona__estado=EstadoPersona.ACTIVO,
            unidad__grupo=grupo,
        )
        adultos_qs = Adulto.objects.select_related("persona").filter(
            persona__estado=EstadoPersona.ACTIVO,
            asignaciones_unidad__unidad__grupo=grupo,
        ).distinct()

        total_beneficiarios_activos = beneficiarios_qs.count()
        total_adultos_activos = adultos_qs.count()
        total_miembros = total_beneficiarios_activos + total_adultos_activos

        adultos_con_formacion = adultos_qs.filter(grados_formacion__isnull=False).distinct().count()
        beneficiarios_con_apoderado_activo = beneficiarios_qs.filter(
            relaciones_apoderados__apoderado__persona__estado=EstadoPersona.ACTIVO
        ).distinct().count()

        cumpleanos_semana = []

        for beneficiario in beneficiarios_qs:
            proximo_cumple = _proximo_cumpleanos(beneficiario.persona.fecha_nacimiento, hoy)
            dias_restantes = (proximo_cumple - hoy).days
            if 0 <= dias_restantes <= 7:
                cumpleanos_semana.append(
                    {
                        "persona_id": beneficiario.persona_id,
                        "tipo": "BENEFICIARIO",
                        "rut": beneficiario.persona.rut,
                        "nombres": beneficiario.persona.nombres,
                        "apellidos": beneficiario.persona.apellidos,
                        "fecha_nacimiento": beneficiario.persona.fecha_nacimiento,
                        "cumpleanos": proximo_cumple,
                        "edad_cumple": _edad_en_fecha(beneficiario.persona.fecha_nacimiento, proximo_cumple),
                        "dias_restantes": dias_restantes,
                        "unidad": {
                            "id": beneficiario.unidad_id,
                            "nombre": beneficiario.unidad.nombre,
                        },
                    }
                )

        for adulto in adultos_qs:
            proximo_cumple = _proximo_cumpleanos(adulto.persona.fecha_nacimiento, hoy)
            dias_restantes = (proximo_cumple - hoy).days
            if 0 <= dias_restantes <= 7:
                cumpleanos_semana.append(
                    {
                        "persona_id": adulto.persona_id,
                        "tipo": "ADULTO",
                        "rut": adulto.persona.rut,
                        "nombres": adulto.persona.nombres,
                        "apellidos": adulto.persona.apellidos,
                        "fecha_nacimiento": adulto.persona.fecha_nacimiento,
                        "cumpleanos": proximo_cumple,
                        "edad_cumple": _edad_en_fecha(adulto.persona.fecha_nacimiento, proximo_cumple),
                        "dias_restantes": dias_restantes,
                    }
                )

        cumpleanos_semana.sort(key=lambda item: (item["dias_restantes"], item["apellidos"], item["nombres"]))

        payload = {
            "grupo": {
                "id": grupo.id,
                "nombre_oficial": grupo.nombre_oficial,
                "estado_vigencia": grupo.estado_vigencia,
            },
            "kpis": {
                "total_miembros": total_miembros,
                "total_beneficiarios_activos": total_beneficiarios_activos,
                "total_adultos_activos": total_adultos_activos,
                "adultos_con_formacion": adultos_con_formacion,
                "porcentaje_adultos_con_formacion": _porcentaje(adultos_con_formacion, total_adultos_activos),
                "beneficiarios_con_apoderado_activo": beneficiarios_con_apoderado_activo,
                "porcentaje_beneficiarios_con_apoderado_activo": _porcentaje(
                    beneficiarios_con_apoderado_activo,
                    total_beneficiarios_activos,
                ),
            },
            "alertas": {
                "cumpleanos_semana": cumpleanos_semana,
            },
        }
        return success_response(data=payload, message="Dashboard del grupo")

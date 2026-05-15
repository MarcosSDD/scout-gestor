from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView

from api.v1.organizacion.serializers import (
    GrupoScoutDetailSerializer,
    GrupoScoutListSerializer,
    GrupoScoutWriteSerializer,
)
from api.v1.responses import success_response
from organizacion.models import GrupoScout
from personas.models import EstadoPersona


class GrupoScoutListCreateView(GenericAPIView):
    def get_queryset(self):
        queryset = GrupoScout.objects.select_related("zona", "distrito").annotate(
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
        serializer = GrupoScoutWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = GrupoScoutDetailSerializer(instance).data
        return success_response(data=payload, message="Grupo creado", status_code=status.HTTP_201_CREATED)


class GrupoScoutRetrieveUpdateView(GenericAPIView):
    queryset = GrupoScout.objects.select_related("zona", "distrito")

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = GrupoScoutDetailSerializer(instance)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = GrupoScoutWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        payload = GrupoScoutDetailSerializer(instance).data
        return success_response(data=payload, message="Grupo actualizado")


class GrupoScoutCalcularMinimoView(APIView):
    def post(self, request, pk):
        instance = get_object_or_404(GrupoScout, pk=pk)
        minimo = instance.recalcular_minimo_miembros(save=True)
        payload = {
            "id": instance.id,
            "minimo_miembros_calculado": minimo,
            "estado_vigencia": instance.estado_vigencia,
        }
        return success_response(data=payload, message="Minimo recalculado")

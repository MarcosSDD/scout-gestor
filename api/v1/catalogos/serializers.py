from rest_framework import serializers

from catalogos.models import Distrito, Rama, Zona


class ZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zona
        fields = ("id", "nombre")


class DistritoSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True)

    class Meta:
        model = Distrito
        fields = ("id", "nombre", "zona", "zona_nombre")


class RamaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rama
        fields = (
            "id",
            "nombre",
            "edad_minima",
            "edad_maxima",
            "composicion_permitida",
            "nomenclatura_subgrupos",
            "activa",
        )

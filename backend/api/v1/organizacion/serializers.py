from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from organizacion.models import GrupoScout


class GrupoScoutListSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True)
    distrito_nombre = serializers.CharField(source="distrito.nombre", read_only=True)
    total_beneficiarios_activos = serializers.IntegerField(read_only=True)
    total_adultos_activos = serializers.IntegerField(read_only=True)

    class Meta:
        model = GrupoScout
        fields = (
            "id",
            "nombre_oficial",
            "zona",
            "zona_nombre",
            "distrito",
            "distrito_nombre",
            "tipo_grupo",
            "estado_vigencia",
            "comuna",
            "logo",
            "minimo_miembros_calculado",
            "total_beneficiarios_activos",
            "total_adultos_activos",
        )


class GrupoScoutDetailSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True)
    distrito_nombre = serializers.CharField(source="distrito.nombre", read_only=True)

    class Meta:
        model = GrupoScout
        fields = (
            "id",
            "nombre_oficial",
            "zona",
            "zona_nombre",
            "distrito",
            "distrito_nombre",
            "tipo_grupo",
            "religion",
            "estado_vigencia",
            "direccion",
            "comuna",
            "referencia",
            "latitud",
            "longitud",
            "logo",
            "minimo_miembros_calculado",
            "created_at",
            "updated_at",
        )


class GrupoScoutWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoScout
        fields = (
            "nombre_oficial",
            "zona",
            "distrito",
            "tipo_grupo",
            "religion",
            "estado_vigencia",
            "direccion",
            "comuna",
            "referencia",
            "latitud",
            "longitud",
            "logo",
        )

    def _run_model_validation(self, instance: GrupoScout):
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            raise serializers.ValidationError(details) from exc

    def validate(self, attrs):
        if self.instance is None:
            candidate = GrupoScout(**attrs)
            self._run_model_validation(candidate)

        return attrs

    def create(self, validated_data):
        instance = GrupoScout(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance

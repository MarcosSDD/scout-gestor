from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from unidades.models import AdultoUnidadRol, Subgrupo, SubgrupoMiembro, Unidad


class ModelValidationMixin:
    def _run_model_validation(self, instance):
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            raise serializers.ValidationError(details) from exc


class UnidadListSerializer(serializers.ModelSerializer):
    grupo_nombre = serializers.CharField(source="grupo.nombre_oficial", read_only=True)
    rama_nombre = serializers.CharField(source="rama.nombre", read_only=True)

    class Meta:
        model = Unidad
        fields = (
            "id",
            "grupo",
            "grupo_nombre",
            "rama",
            "rama_nombre",
            "nombre",
            "tipo_composicion",
            "estado",
            "cupo_maximo",
        )


class UnidadDetailSerializer(serializers.ModelSerializer):
    grupo_nombre = serializers.CharField(source="grupo.nombre_oficial", read_only=True)
    rama_nombre = serializers.CharField(source="rama.nombre", read_only=True)

    class Meta:
        model = Unidad
        fields = (
            "id",
            "grupo",
            "grupo_nombre",
            "rama",
            "rama_nombre",
            "nombre",
            "tipo_composicion",
            "estado",
            "cupo_maximo",
            "created_at",
            "updated_at",
        )


class UnidadWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Unidad
        fields = (
            "grupo",
            "rama",
            "nombre",
            "tipo_composicion",
            "estado",
            "cupo_maximo",
        )

    def validate(self, attrs):
        if self.instance is None:
            candidate = Unidad(**attrs)
            self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        instance = Unidad(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance


class AdultoUnidadRolListSerializer(serializers.ModelSerializer):
    unidad_nombre = serializers.CharField(source="unidad.nombre", read_only=True)
    adulto_persona_nombre = serializers.SerializerMethodField()

    class Meta:
        model = AdultoUnidadRol
        fields = (
            "id",
            "unidad",
            "unidad_nombre",
            "adulto",
            "adulto_persona_nombre",
            "rol",
        )

    def get_adulto_persona_nombre(self, obj):
        return f"{obj.adulto.persona.nombres} {obj.adulto.persona.apellidos}"


class AdultoUnidadRolWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = AdultoUnidadRol
        fields = (
            "unidad",
            "adulto",
            "rol",
        )

    def validate(self, attrs):
        if self.instance is None:
            candidate = AdultoUnidadRol(**attrs)
            self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        instance = AdultoUnidadRol(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance


class SubgrupoListSerializer(serializers.ModelSerializer):
    unidad_nombre = serializers.CharField(source="unidad.nombre", read_only=True)

    class Meta:
        model = Subgrupo
        fields = (
            "id",
            "nombre",
            "unidad",
            "unidad_nombre",
            "lider_juvenil",
        )


class SubgrupoWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Subgrupo
        fields = (
            "nombre",
            "unidad",
            "lider_juvenil",
        )

    def validate(self, attrs):
        if self.instance is None:
            candidate = Subgrupo(**attrs)
            self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        instance = Subgrupo(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance


class SubgrupoMiembroListSerializer(serializers.ModelSerializer):
    subgrupo_nombre = serializers.CharField(source="subgrupo.nombre", read_only=True)
    beneficiario_persona_nombre = serializers.SerializerMethodField()

    class Meta:
        model = SubgrupoMiembro
        fields = (
            "id",
            "subgrupo",
            "subgrupo_nombre",
            "beneficiario",
            "beneficiario_persona_nombre",
        )

    def get_beneficiario_persona_nombre(self, obj):
        return f"{obj.beneficiario.persona.nombres} {obj.beneficiario.persona.apellidos}"


class SubgrupoMiembroWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = SubgrupoMiembro
        fields = (
            "subgrupo",
            "beneficiario",
        )

    def validate(self, attrs):
        if self.instance is None:
            candidate = SubgrupoMiembro(**attrs)
            self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        instance = SubgrupoMiembro(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance


class SubgrupoMiembroReasignacionSerializer(serializers.Serializer):
    subgrupo = serializers.PrimaryKeyRelatedField(queryset=Subgrupo.objects.all())


class OpcionGrupoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField(source="nombre_oficial")


class OpcionUnidadSerializer(serializers.ModelSerializer):
    grupo_nombre = serializers.CharField(source="grupo.nombre_oficial", read_only=True)

    class Meta:
        model = Unidad
        fields = ("id", "nombre", "grupo_nombre", "rama", "estado")


class OpcionUnidadQuerySerializer(serializers.Serializer):
    rama_id = serializers.IntegerField(required=True, min_value=1)


class OpcionPersonaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.SerializerMethodField()

    def get_nombre(self, obj):
        return f"{obj.persona.nombres} {obj.persona.apellidos}"


class OpcionDestinoMembresiaSerializer(serializers.ModelSerializer):
    unidad_nombre = serializers.CharField(source="unidad.nombre", read_only=True)

    class Meta:
        model = Subgrupo
        fields = ("id", "nombre", "unidad", "unidad_nombre")

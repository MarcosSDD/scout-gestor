from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from common.validators import normalizar_rut, validar_rut
from personas.models import Adulto, Apoderado, ApoderadoBeneficiario, Beneficiario, EstadoPersona, Persona, RolAdulto


class ModelValidationMixin:
    def _run_model_validation(self, instance):
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            raise serializers.ValidationError(details) from exc


class PersonaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = (
            "id",
            "rut",
            "nombres",
            "apellidos",
            "sexo",
            "estado",
            "telefono",
            "email",
        )


class PersonaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = (
            "id",
            "rut",
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "sexo",
            "direccion",
            "telefono",
            "email",
            "estado",
            "created_at",
            "updated_at",
        )


class PersonaWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = (
            "rut",
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "sexo",
            "direccion",
            "telefono",
            "email",
            "estado",
        )

    def validate_rut(self, value):
        normalized = normalizar_rut(value)
        validar_rut(normalized)
        return normalized

    def validate(self, attrs):
        if self.instance is None:
            candidate = Persona(**attrs)
            self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        instance = Persona(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance


class AdultoListSerializer(serializers.ModelSerializer):
    persona_rut = serializers.CharField(source="persona.rut", read_only=True)
    persona_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Adulto
        fields = (
            "id",
            "persona",
            "persona_rut",
            "persona_nombre",
            "rol_principal",
            "certificado_inhabilidades",
            "certificado_vigencia_hasta",
        )

    def get_persona_nombre(self, obj):
        return f"{obj.persona.nombres} {obj.persona.apellidos}"


class AdultoDetailSerializer(serializers.ModelSerializer):
    persona = PersonaDetailSerializer(read_only=True)

    class Meta:
        model = Adulto
        fields = (
            "id",
            "persona",
            "rol_principal",
            "certificado_inhabilidades",
            "certificado_vigencia_hasta",
            "created_at",
            "updated_at",
        )


class AdultoWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    certificado_inhabilidades = serializers.CharField()

    class Meta:
        model = Adulto
        fields = (
            "persona",
            "rol_principal",
            "certificado_inhabilidades",
            "certificado_vigencia_hasta",
        )

    def validate(self, attrs):
        if self.instance is None:
            candidate = Adulto(**attrs)
            self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        instance = Adulto(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        if instance.rol_principal == RolAdulto.APODERADO:
            Apoderado.objects.get_or_create(persona=instance.persona)
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        if instance.rol_principal == RolAdulto.APODERADO:
            Apoderado.objects.get_or_create(persona=instance.persona)
        return instance


class BeneficiarioListSerializer(serializers.ModelSerializer):
    persona_rut = serializers.CharField(source="persona.rut", read_only=True)
    persona_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiario
        fields = (
            "id",
            "persona",
            "persona_rut",
            "persona_nombre",
            "rama_actual",
            "unidad",
            "fecha_ingreso",
        )

    def get_persona_nombre(self, obj):
        return f"{obj.persona.nombres} {obj.persona.apellidos}"


class BeneficiarioDetailSerializer(serializers.ModelSerializer):
    persona = PersonaDetailSerializer(read_only=True)

    class Meta:
        model = Beneficiario
        fields = (
            "id",
            "persona",
            "rama_actual",
            "unidad",
            "fecha_ingreso",
            "progresion_scout",
            "created_at",
            "updated_at",
        )


class BeneficiarioWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Beneficiario
        fields = (
            "persona",
            "rama_actual",
            "unidad",
            "fecha_ingreso",
            "progresion_scout",
        )

    def validate(self, attrs):
        if self.instance is None:
            candidate = Beneficiario(**attrs)
            self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        instance = Beneficiario(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance


class ApoderadoListSerializer(serializers.ModelSerializer):
    persona_rut = serializers.CharField(source="persona.rut", read_only=True)
    persona_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Apoderado
        fields = (
            "id",
            "persona",
            "persona_rut",
            "persona_nombre",
            "es_miembro_comite",
            "rol_comite",
        )

    def get_persona_nombre(self, obj):
        return f"{obj.persona.nombres} {obj.persona.apellidos}"


class ApoderadoDetailSerializer(serializers.ModelSerializer):
    persona = PersonaDetailSerializer(read_only=True)

    class Meta:
        model = Apoderado
        fields = (
            "id",
            "persona",
            "es_miembro_comite",
            "rol_comite",
            "created_at",
            "updated_at",
        )


class ApoderadoWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Apoderado
        fields = (
            "persona",
            "es_miembro_comite",
            "rol_comite",
        )

    def validate(self, attrs):
        if self.instance is None:
            candidate = Apoderado(**attrs)
            self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        instance = Apoderado(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance


class ApoderadoBeneficiarioListSerializer(serializers.ModelSerializer):
    apoderado_persona_nombre = serializers.SerializerMethodField()
    beneficiario_persona_nombre = serializers.SerializerMethodField()

    class Meta:
        model = ApoderadoBeneficiario
        fields = (
            "id",
            "apoderado",
            "apoderado_persona_nombre",
            "beneficiario",
            "beneficiario_persona_nombre",
            "parentesco",
            "autoriza_salidas_terreno",
            "fecha_autorizacion",
        )

    def get_apoderado_persona_nombre(self, obj):
        return f"{obj.apoderado.persona.nombres} {obj.apoderado.persona.apellidos}"

    def get_beneficiario_persona_nombre(self, obj):
        return f"{obj.beneficiario.persona.nombres} {obj.beneficiario.persona.apellidos}"


class ApoderadoBeneficiarioWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = ApoderadoBeneficiario
        fields = (
            "apoderado",
            "beneficiario",
            "parentesco",
            "autoriza_salidas_terreno",
            "fecha_autorizacion",
        )

    def validate(self, attrs):
        relation = self.instance or ApoderadoBeneficiario(**attrs)

        if self.instance:
            for key, value in attrs.items():
                setattr(relation, key, value)

        if relation.autoriza_salidas_terreno and not relation.fecha_autorizacion:
            raise serializers.ValidationError({"fecha_autorizacion": "La fecha es obligatoria cuando autoriza salidas"})

        if relation.apoderado.persona.estado != EstadoPersona.ACTIVO:
            raise serializers.ValidationError({"apoderado": "El apoderado debe estar activo"})

        if relation.beneficiario.persona.estado != EstadoPersona.ACTIVO:
            raise serializers.ValidationError({"beneficiario": "El beneficiario debe estar activo"})

        if self.instance is None:
            self._run_model_validation(relation)
        return attrs

    def create(self, validated_data):
        instance = ApoderadoBeneficiario(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        return instance


class ValidarRutSerializer(serializers.Serializer):
    rut = serializers.CharField()

    def validate_rut(self, value):
        normalized = normalizar_rut(value)
        validar_rut(normalized)
        return normalized

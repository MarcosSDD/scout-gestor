from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from common.validators import normalizar_rut, validar_rut
from api.v1.access import (
    can_download_adulto_certificate,
    can_view_expanded_persona_pii,
    can_view_operational_persona_pii,
    can_view_persona_photo,
)
from personas.models import (
    Adulto,
    Apoderado,
    ApoderadoBeneficiario,
    AreaDesarrollo,
    Beneficiario,
    EstadoPersona,
    Persona,
    RegistroProgresionScout,
    RolAdulto,
)


class ModelValidationMixin:
    def _run_model_validation(self, instance, exclude=None):
        try:
            instance.full_clean(exclude=exclude)
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            raise serializers.ValidationError(details) from exc


class PersonaListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Persona
        fields = (
            "id",
            "nombre_completo",
            "estado",
        )

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"


class PersonaDetailSerializer(serializers.ModelSerializer):
    foto_disponible = serializers.SerializerMethodField()

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
            "foto_disponible",
            "estado",
            "created_at",
            "updated_at",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context.get("request").user if self.context.get("request") else None
        if can_view_expanded_persona_pii(user, instance):
            return data
        if can_view_operational_persona_pii(user, instance):
            for field in ("rut", "direccion"):
                data.pop(field, None)
            return data
        for field in ("rut", "fecha_nacimiento", "direccion", "telefono", "email"):
            data.pop(field, None)
        return data

    def get_foto_disponible(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return bool(obj.foto and can_view_persona_photo(user, obj))


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
            "foto",
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
    persona_nombre = serializers.SerializerMethodField()
    persona_estado = serializers.CharField(source="persona.estado", read_only=True)
    certificado_vigente = serializers.BooleanField(read_only=True)

    class Meta:
        model = Adulto
        fields = (
            "id",
            "persona",
            "persona_nombre",
            "persona_estado",
            "rol_principal",
            "certificado_vigencia_hasta",
            "certificado_vigente",
        )

    def get_persona_nombre(self, obj):
        return f"{obj.persona.nombres} {obj.persona.apellidos}"

class AdultoDetailSerializer(serializers.ModelSerializer):
    persona = PersonaDetailSerializer(read_only=True)
    certificado_vigente = serializers.BooleanField(read_only=True)
    certificado_disponible = serializers.SerializerMethodField()

    class Meta:
        model = Adulto
        fields = (
            "id",
            "persona",
            "rol_principal",
            "certificado_vigencia_hasta",
            "certificado_vigente",
            "certificado_disponible",
            "created_at",
            "updated_at",
        )

    def get_certificado_disponible(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return bool(obj.certificado_inhabilidades and can_download_adulto_certificate(user, obj))

class AdultoWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
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


class AdultoCertificadoRenewalSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Adulto
        fields = (
            "certificado_inhabilidades",
            "certificado_vigencia_hasta",
        )

    def validate(self, attrs):
        if not self.instance:
            return attrs
        candidate = Adulto(
            pk=self.instance.pk,
            persona=self.instance.persona,
            rol_principal=self.instance.rol_principal,
            certificado_inhabilidades=attrs.get("certificado_inhabilidades", self.instance.certificado_inhabilidades),
            certificado_vigencia_hasta=attrs.get("certificado_vigencia_hasta", self.instance.certificado_vigencia_hasta),
        )
        self._run_model_validation(candidate, exclude={"id", "persona"})
        return attrs

class BeneficiarioListSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.SerializerMethodField()
    persona_estado = serializers.CharField(source="persona.estado", read_only=True)
    rama_nombre = serializers.CharField(source="rama_actual.nombre", read_only=True, default=None)
    unidad_nombre = serializers.CharField(source="unidad.nombre", read_only=True, default=None)
    grupo = serializers.IntegerField(source="unidad.grupo_id", read_only=True, default=None)
    grupo_nombre = serializers.CharField(source="unidad.grupo.nombre_oficial", read_only=True, default=None)

    class Meta:
        model = Beneficiario
        fields = (
            "id",
            "persona",
            "persona_nombre",
            "persona_estado",
            "rama_actual",
            "rama_nombre",
            "unidad",
            "unidad_nombre",
            "grupo",
            "grupo_nombre",
            "fecha_ingreso",
        )

    def get_persona_nombre(self, obj):
        return f"{obj.persona.nombres} {obj.persona.apellidos}"


class BeneficiarioDetailSerializer(serializers.ModelSerializer):
    persona = PersonaDetailSerializer(read_only=True)
    registros_progresion_recientes = serializers.SerializerMethodField()
    rama_nombre = serializers.CharField(source="rama_actual.nombre", read_only=True, default=None)
    unidad_nombre = serializers.CharField(source="unidad.nombre", read_only=True, default=None)
    grupo_nombre = serializers.CharField(source="unidad.grupo.nombre_oficial", read_only=True, default=None)

    class Meta:
        model = Beneficiario
        fields = (
            "id",
            "persona",
            "rama_actual",
            "rama_nombre",
            "unidad",
            "unidad_nombre",
            "grupo_nombre",
            "fecha_ingreso",
            "registros_progresion_recientes",
            "created_at",
            "updated_at",
        )

    def get_registros_progresion_recientes(self, obj):
        request = self.context.get("request")
        from api.v1.access import can_edit_beneficiario

        if not request or not can_edit_beneficiario(request.user, obj):
            return []
        registros = obj.registros_progresion.prefetch_related("areas").all()[:5]
        return RegistroProgresionScoutListSerializer(registros, many=True, context=self.context).data


class BeneficiarioWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Beneficiario
        fields = (
            "persona",
            "rama_actual",
            "unidad",
            "fecha_ingreso",
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


class BeneficiarioAsignacionSerializer(ModelValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Beneficiario
        fields = (
            "rama_actual",
            "unidad",
        )

    def validate(self, attrs):
        unidad = attrs.get("unidad")
        rama_actual = attrs.get("rama_actual")
        errors = {}
        if unidad is None:
            errors["unidad"] = "La unidad de destino es obligatoria"
        if rama_actual is None:
            errors["rama_actual"] = "La rama actual es obligatoria"
        if unidad and rama_actual and unidad.rama_id != rama_actual.id:
            errors["rama_actual"] = "La rama actual debe coincidir con la rama de la unidad"
        if errors:
            raise serializers.ValidationError(errors)

        candidate = Beneficiario(
            pk=self.instance.pk if self.instance else None,
            persona=self.instance.persona if self.instance else None,
            rama_actual=rama_actual,
            unidad=unidad,
            fecha_ingreso=self.instance.fecha_ingreso if self.instance else None,
        )
        self._run_model_validation(candidate, exclude={"id", "persona"})
        return attrs

class AreaDesarrolloSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaDesarrollo
        fields = (
            "id",
            "codigo",
            "nombre",
            "definicion",
            "personaje_simbolo",
            "lema",
        )


class RegistroProgresionScoutListSerializer(serializers.ModelSerializer):
    beneficiario_persona_nombre = serializers.SerializerMethodField()
    areas = AreaDesarrolloSerializer(many=True, read_only=True)

    class Meta:
        model = RegistroProgresionScout
        fields = (
            "id",
            "beneficiario",
            "beneficiario_persona_nombre",
            "fecha",
            "tipo",
            "texto",
            "areas",
            "created_at",
            "updated_at",
        )

    def get_beneficiario_persona_nombre(self, obj):
        return f"{obj.beneficiario.persona.nombres} {obj.beneficiario.persona.apellidos}"


class RegistroProgresionScoutWriteSerializer(ModelValidationMixin, serializers.ModelSerializer):
    areas = serializers.PrimaryKeyRelatedField(queryset=AreaDesarrollo.objects.all(), many=True)

    class Meta:
        model = RegistroProgresionScout
        fields = (
            "beneficiario",
            "fecha",
            "tipo",
            "texto",
            "areas",
        )

    def validate(self, attrs):
        areas = attrs.get("areas")
        if self.instance is None and not areas:
            raise serializers.ValidationError({"areas": "Debe seleccionar al menos un area de desarrollo"})
        if self.instance is not None and "areas" in attrs and not areas:
            raise serializers.ValidationError({"areas": "Debe seleccionar al menos un area de desarrollo"})

        fecha = attrs.get("fecha", getattr(self.instance, "fecha", None))
        if fecha and fecha > timezone.localdate():
            raise serializers.ValidationError({"fecha": "La fecha no puede ser futura"})

        candidate_data = attrs.copy()
        candidate_data.pop("areas", None)
        if self.instance is None:
            candidate = RegistroProgresionScout(**candidate_data)
        else:
            candidate = self.instance
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
        self._run_model_validation(candidate)
        return attrs

    def create(self, validated_data):
        areas = validated_data.pop("areas")
        instance = RegistroProgresionScout(**validated_data)
        self._run_model_validation(instance)
        instance.save()
        instance.areas.set(areas)
        return instance

    def update(self, instance, validated_data):
        areas = validated_data.pop("areas", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self._run_model_validation(instance)
        instance.save()
        if areas is not None:
            instance.areas.set(areas)
        return instance

class ApoderadoListSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.SerializerMethodField()
    persona_estado = serializers.CharField(source="persona.estado", read_only=True)

    class Meta:
        model = Apoderado
        fields = (
            "id",
            "persona",
            "persona_nombre",
            "persona_estado",
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

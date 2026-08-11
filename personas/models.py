from django.db import models
from django.conf import settings
from pathlib import Path
from uuid import uuid4

from common.models import TimeStampedModel
from common.validators import normalizar_rut, validar_certificado_inhabilidades, validar_foto_persona, validar_rut
from simple_history.models import HistoricalRecords


def private_persona_foto_upload_to(instance, filename):
    return f"personas/fotos/{uuid4().hex}{Path(filename).suffix.lower()}"


def private_certificado_upload_to(instance, filename):
    return f"certificados_inhabilidades/{uuid4().hex}{Path(filename).suffix.lower()}"


class EstadoPersona(models.TextChoices):
    ACTIVO = "ACTIVO", "Activo"
    INACTIVO = "INACTIVO", "Inactivo"


class SexoPersona(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"
    NO_BINARIO = "NB", "No binario"
    OTRO = "OT", "Otro"


class RolAdulto(models.TextChoices):
    GUIA = "GUIA", "Guia"
    DIRIGENTE = "DIRIGENTE", "Dirigente"
    APODERADO = "APODERADO", "Apoderado"
    RESP_GRUPO = "RESP_GRUPO", "Responsable de grupo"
    COLABORADOR = "COLABORADOR", "Colaborador"


class Parentesco(models.TextChoices):
    PADRE = "PADRE", "Padre"
    MADRE = "MADRE", "Madre"
    TUTOR = "TUTOR", "Tutor"
    ABUELO = "ABUELO", "Abuelo/a"
    OTRO = "OTRO", "Otro"


class TipoRegistroProgresion(models.TextChoices):
    INICIO_CICLO = "INICIO_CICLO", "Inicio ciclo"
    DURANTE_CICLO = "DURANTE_CICLO", "Durante el ciclo"
    FINAL_CICLO = "FINAL_CICLO", "Final de ciclo"


class Persona(TimeStampedModel):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="persona",
    )
    rut = models.CharField(max_length=12, unique=True, validators=[validar_rut])
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=2, choices=SexoPersona.choices)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    foto = models.ImageField(upload_to=private_persona_foto_upload_to, blank=True, null=True, validators=[validar_foto_persona])
    estado = models.CharField(max_length=10, choices=EstadoPersona.choices, default=EstadoPersona.ACTIVO)
    history = HistoricalRecords()

    class Meta:
        ordering = ["apellidos", "nombres"]
        verbose_name = "Persona"
        verbose_name_plural = "Personas"

    def __str__(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)


class Adulto(TimeStampedModel):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name="adulto")
    rol_principal = models.CharField(max_length=20, choices=RolAdulto.choices)
    certificado_inhabilidades = models.FileField(upload_to=private_certificado_upload_to, validators=[validar_certificado_inhabilidades])
    certificado_vigencia_hasta = models.DateField()
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Adulto"
        verbose_name_plural = "Adultos"

    def __str__(self) -> str:
        return f"Adulto: {self.persona}"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        if not self.certificado_inhabilidades:
            raise ValidationError({"certificado_inhabilidades": "El certificado es obligatorio"})
        if self.certificado_vigencia_hasta < timezone.localdate():
            raise ValidationError({"certificado_vigencia_hasta": "El certificado no puede estar vencido"})

        hoy = timezone.localdate()
        edad = hoy.year - self.persona.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (self.persona.fecha_nacimiento.month, self.persona.fecha_nacimiento.day):
            edad -= 1
        if edad < 18:
            raise ValidationError({"persona": "El adulto debe ser mayor o igual a 18 anos"})

        roles_dirigencia = {RolAdulto.GUIA, RolAdulto.DIRIGENTE, RolAdulto.RESP_GRUPO}
        if self.rol_principal in roles_dirigencia and hasattr(self.persona, "beneficiario"):
            raise ValidationError({"persona": "Un beneficiario no puede ser registrado como dirigente"})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.rol_principal == RolAdulto.APODERADO:
            Apoderado.objects.get_or_create(persona=self.persona)

    @property
    def certificado_vigente(self) -> bool:
        from django.utils import timezone

        return self.certificado_vigencia_hasta >= timezone.localdate()


class Apoderado(TimeStampedModel):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name="apoderado")
    es_miembro_comite = models.BooleanField(default=False)
    rol_comite = models.CharField(max_length=20, blank=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Apoderado"
        verbose_name_plural = "Apoderados"

    def __str__(self) -> str:
        return f"Apoderado: {self.persona}"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        hoy = timezone.localdate()
        edad = hoy.year - self.persona.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (self.persona.fecha_nacimiento.month, self.persona.fecha_nacimiento.day):
            edad -= 1
        if edad < 18:
            raise ValidationError({"persona": "El apoderado debe ser mayor o igual a 18 anos"})


class Beneficiario(TimeStampedModel):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name="beneficiario")
    rama_actual = models.ForeignKey(
        "catalogos.Rama",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="beneficiarios",
    )
    unidad = models.ForeignKey(
        "unidades.Unidad",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="beneficiarios",
    )
    fecha_ingreso = models.DateField()
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Beneficiario"
        verbose_name_plural = "Beneficiarios"

    def __str__(self) -> str:
        return f"Beneficiario: {self.persona}"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        from catalogos.models import ComposicionPermitida

        if self.unidad_id and self.rama_actual_id and self.unidad.rama_id != self.rama_actual_id:
            raise ValidationError({"rama_actual": "La rama actual debe coincidir con la rama de la unidad"})

        if self.unidad_id:
            if self.persona.estado == EstadoPersona.ACTIVO and self.unidad.cupo_maximo is not None:
                activos = Beneficiario.objects.filter(
                    unidad_id=self.unidad_id, persona__estado=EstadoPersona.ACTIVO
                ).exclude(pk=self.pk).count()
                if activos >= self.unidad.cupo_maximo:
                    raise ValidationError({"unidad": "La unidad no tiene cupos disponibles."})
            composicion = self.unidad.composicion_actual()
            sexo = self.persona.sexo

            if composicion == ComposicionPermitida.SOLO_HOMBRES and sexo != SexoPersona.MASCULINO:
                raise ValidationError({"persona": "La unidad permite solo beneficiarios hombres"})

            if composicion == ComposicionPermitida.SOLO_MUJERES and sexo != SexoPersona.FEMENINO:
                raise ValidationError({"persona": "La unidad permite solo beneficiarias mujeres"})


class AreaDesarrollo(TimeStampedModel):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=80)
    definicion = models.TextField()
    personaje_simbolo = models.CharField(max_length=80, blank=True)
    lema = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Area de desarrollo"
        verbose_name_plural = "Areas de desarrollo"

    def __str__(self) -> str:
        return self.nombre


class RegistroProgresionScout(TimeStampedModel):
    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE, related_name="registros_progresion")
    fecha = models.DateField()
    tipo = models.CharField(max_length=20, choices=TipoRegistroProgresion.choices)
    texto = models.TextField()
    areas = models.ManyToManyField(AreaDesarrollo, related_name="registros_progresion")
    history = HistoricalRecords(m2m_fields=[areas])

    class Meta:
        ordering = ["-fecha", "-created_at"]
        verbose_name = "Registro de progresion scout"
        verbose_name_plural = "Registros de progresion scout"

    def __str__(self) -> str:
        return f"{self.beneficiario.persona} - {self.get_tipo_display()} - {self.fecha}"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        if not self.texto or not self.texto.strip():
            raise ValidationError({"texto": "El texto de progresion es obligatorio"})

        if self.fecha and self.fecha > timezone.localdate():
            raise ValidationError({"fecha": "La fecha no puede ser futura"})

        if self.beneficiario_id and self.beneficiario.persona.estado != EstadoPersona.ACTIVO:
            raise ValidationError({"beneficiario": "El beneficiario debe estar activo"})


class ApoderadoBeneficiario(TimeStampedModel):
    apoderado = models.ForeignKey(
        Apoderado,
        on_delete=models.CASCADE,
        related_name="relaciones_beneficiarios",
    )
    beneficiario = models.ForeignKey(
        Beneficiario,
        on_delete=models.CASCADE,
        related_name="relaciones_apoderados",
    )
    parentesco = models.CharField(max_length=20, choices=Parentesco.choices)
    autoriza_salidas_terreno = models.BooleanField(default=False)
    fecha_autorizacion = models.DateField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["apoderado", "beneficiario"],
                name="uq_apoderado_beneficiario",
            )
        ]
        verbose_name = "Relacion apoderado-beneficiario"
        verbose_name_plural = "Relaciones apoderado-beneficiario"

    def __str__(self) -> str:
        return f"{self.apoderado.persona} -> {self.beneficiario.persona}"

# Create your models here.

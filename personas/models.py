from django.db import models

from common.models import TimeStampedModel
from common.validators import normalizar_rut, validar_foto_persona, validar_rut


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


class Persona(TimeStampedModel):
    rut = models.CharField(max_length=12, unique=True, validators=[validar_rut])
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=2, choices=SexoPersona.choices)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    foto = models.ImageField(upload_to="personas/fotos/", blank=True, null=True, validators=[validar_foto_persona])
    estado = models.CharField(max_length=10, choices=EstadoPersona.choices, default=EstadoPersona.ACTIVO)

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
    certificado_inhabilidades = models.FileField(upload_to="certificados_inhabilidades/")
    certificado_vigencia_hasta = models.DateField()

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
    progresion_scout = models.TextField(blank=True)

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
            composicion = self.unidad.composicion_actual()
            sexo = self.persona.sexo

            if composicion == ComposicionPermitida.SOLO_HOMBRES and sexo != SexoPersona.MASCULINO:
                raise ValidationError({"persona": "La unidad permite solo beneficiarios hombres"})

            if composicion == ComposicionPermitida.SOLO_MUJERES and sexo != SexoPersona.FEMENINO:
                raise ValidationError({"persona": "La unidad permite solo beneficiarias mujeres"})


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

from django.db import models

from catalogos.models import ComposicionPermitida
from common.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class EstadoUnidad(models.TextChoices):
    ACTIVA = "ACTIVA", "Activa"
    INACTIVA = "INACTIVA", "Inactiva"


class RolAdultoUnidad(models.TextChoices):
    RESPONSABLE = "RESPONSABLE", "Responsable de unidad"
    ASISTENTE = "ASISTENTE", "Asistente"
    COLABORADOR = "COLABORADOR", "Colaborador"


class Unidad(TimeStampedModel):
    grupo = models.ForeignKey("organizacion.GrupoScout", on_delete=models.CASCADE, related_name="unidades")
    rama = models.ForeignKey("catalogos.Rama", on_delete=models.PROTECT, related_name="unidades")
    nombre = models.CharField(max_length=120)
    tipo_composicion = models.CharField(
        max_length=20,
        choices=ComposicionPermitida.choices,
        blank=True,
    )
    estado = models.CharField(max_length=10, choices=EstadoUnidad.choices, default=EstadoUnidad.ACTIVA)
    cupo_maximo = models.PositiveIntegerField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(fields=["grupo", "nombre"], name="uq_unidad_nombre_por_grupo"),
        ]
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"

    def __str__(self) -> str:
        return self.nombre

    def composicion_actual(self) -> str:
        return self.tipo_composicion or self.rama.composicion_permitida

    def clean(self) -> None:
        from django.core.exceptions import ValidationError
        from personas.models import EstadoPersona

        if self.pk and self.cupo_maximo is not None:
            activos = self.beneficiarios.filter(persona__estado=EstadoPersona.ACTIVO).count()
            if activos > self.cupo_maximo:
                raise ValidationError({"cupo_maximo": "El cupo no puede ser menor que los beneficiarios activos."})


class Subgrupo(TimeStampedModel):
    nombre = models.CharField(max_length=100)
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, related_name="subgrupos")
    lider_juvenil = models.ForeignKey(
        "personas.Beneficiario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subgrupos_liderados",
    )
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["unidad", "nombre"], name="uq_subgrupo_nombre_por_unidad"),
        ]
        verbose_name = "Subgrupo"
        verbose_name_plural = "Subgrupos"

    def __str__(self) -> str:
        return f"{self.nombre} ({self.unidad.nombre})"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.lider_juvenil_id:
            if self.lider_juvenil.unidad_id != self.unidad_id:
                raise ValidationError({"lider_juvenil": "El lider juvenil debe pertenecer a la misma unidad"})
            if not SubgrupoMiembro.objects.filter(subgrupo_id=self.pk, beneficiario_id=self.lider_juvenil_id).exists():
                raise ValidationError({"lider_juvenil": "El lider juvenil debe ser miembro actual del subgrupo."})


class SubgrupoMiembro(TimeStampedModel):
    subgrupo = models.ForeignKey(Subgrupo, on_delete=models.CASCADE, related_name="miembros")
    beneficiario = models.ForeignKey("personas.Beneficiario", on_delete=models.CASCADE, related_name="membresias_subgrupo")
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subgrupo", "beneficiario"],
                name="uq_subgrupo_beneficiario",
            )
        ]
        verbose_name = "Miembro de subgrupo"
        verbose_name_plural = "Miembros de subgrupo"

    def __str__(self) -> str:
        return f"{self.beneficiario.persona} en {self.subgrupo.nombre}"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.beneficiario.unidad_id != self.subgrupo.unidad_id:
            raise ValidationError({"beneficiario": "El beneficiario debe pertenecer a la misma unidad del subgrupo"})

        miembro_en_unidad = SubgrupoMiembro.objects.filter(
            beneficiario_id=self.beneficiario_id,
            subgrupo__unidad_id=self.subgrupo.unidad_id,
        ).exclude(pk=self.pk)

        if miembro_en_unidad.exists():
            raise ValidationError({"beneficiario": "El beneficiario ya pertenece a otro subgrupo de la misma unidad"})


class AdultoUnidadRol(TimeStampedModel):
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, related_name="equipo_adulto")
    adulto = models.ForeignKey("personas.Adulto", on_delete=models.PROTECT, related_name="asignaciones_unidad")
    rol = models.CharField(max_length=20, choices=RolAdultoUnidad.choices)
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["unidad", "adulto"],
                name="uq_adulto_por_unidad",
            ),
            models.UniqueConstraint(
                fields=["unidad", "rol"],
                condition=models.Q(rol=RolAdultoUnidad.RESPONSABLE),
                name="uq_responsable_por_unidad",
            ),
        ]
        verbose_name = "Rol adulto en unidad"
        verbose_name_plural = "Roles adultos en unidad"

    def __str__(self) -> str:
        return f"{self.adulto.persona} - {self.get_rol_display()}"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        from personas.models import SexoPersona

        if self.unidad.estado != EstadoUnidad.ACTIVA:
            raise ValidationError({"unidad": "Solo se pueden asignar adultos a unidades activas."})
        if not self.adulto.certificado_vigente:
            raise ValidationError("No se puede asignar un adulto con certificado vencido")

        composicion = self.unidad.composicion_actual()
        sexo = self.adulto.persona.sexo
        if composicion == ComposicionPermitida.SOLO_HOMBRES and sexo != SexoPersona.MASCULINO:
            raise ValidationError("La unidad permite solo adultos hombres")
        if composicion == ComposicionPermitida.SOLO_MUJERES and sexo != SexoPersona.FEMENINO:
            raise ValidationError("La unidad permite solo adultas mujeres")

# Create your models here.

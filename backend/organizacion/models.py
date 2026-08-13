from django.db import models

from common.models import TimeStampedModel
from common.validators import validar_url_o_ruta_logo


class TipoGrupo(models.TextChoices):
    CONFESIONAL = "CONFESIONAL", "Confesional"
    PLURICONFESIONAL = "PLURICONFESIONAL", "Pluriconfesional"


class EstadoVigenciaGrupo(models.TextChoices):
    ACTIVO = "ACTIVO", "Activo"
    SUSPENDIDO = "SUSPENDIDO", "Suspendido"
    DISUELTO = "DISUELTO", "Disuelto"
    OBSERVACION = "OBSERVACION", "Observacion"


class RolComite(models.TextChoices):
    PRESIDENTE = "PRESIDENTE", "Presidente"
    SECRETARIO = "SECRETARIO", "Secretario/a"
    TESORERO = "TESORERO", "Tesorero/a"


class GrupoScout(TimeStampedModel):
    nombre_oficial = models.CharField(max_length=180, unique=True)
    distrito = models.ForeignKey("catalogos.Distrito", on_delete=models.PROTECT, related_name="grupos")
    zona = models.ForeignKey("catalogos.Zona", on_delete=models.PROTECT, related_name="grupos")
    tipo_grupo = models.CharField(max_length=20, choices=TipoGrupo.choices)
    religion = models.CharField(max_length=80, blank=True)
    estado_vigencia = models.CharField(
        max_length=20,
        choices=EstadoVigenciaGrupo.choices,
        default=EstadoVigenciaGrupo.ACTIVO,
    )
    direccion = models.CharField(max_length=200)
    comuna = models.CharField(max_length=80)
    referencia = models.CharField(max_length=200, blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    logo = models.CharField(max_length=500, blank=True, validators=[validar_url_o_ruta_logo])
    minimo_miembros_calculado = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["nombre_oficial"]
        verbose_name = "Grupo Scout"
        verbose_name_plural = "Grupos Scout"

    def __str__(self) -> str:
        return self.nombre_oficial

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.tipo_grupo == TipoGrupo.CONFESIONAL and not self.religion:
            raise ValidationError({"religion": "La religion es obligatoria para grupos confesionales"})

        if self.distrito_id and self.zona_id and self.distrito.zona_id != self.zona_id:
            raise ValidationError({"distrito": "El distrito debe pertenecer a la zona seleccionada"})

    def recalcular_minimo_miembros(self, *, save: bool = True) -> int:
        from personas.models import Adulto, Beneficiario, EstadoPersona

        total_beneficiarios = Beneficiario.objects.filter(
            persona__estado=EstadoPersona.ACTIVO,
            unidad__grupo=self,
        ).count()
        total_adultos = Adulto.objects.filter(
            persona__estado=EstadoPersona.ACTIVO,
            asignaciones_unidad__unidad__grupo=self,
        ).distinct().count()
        self.minimo_miembros_calculado = total_beneficiarios + total_adultos
        if self.minimo_miembros_calculado < 20:
            self.estado_vigencia = EstadoVigenciaGrupo.OBSERVACION
        elif self.estado_vigencia == EstadoVigenciaGrupo.OBSERVACION:
            self.estado_vigencia = EstadoVigenciaGrupo.ACTIVO
        if save:
            self.save(update_fields=["minimo_miembros_calculado", "estado_vigencia", "updated_at"])
        return self.minimo_miembros_calculado


class InstitucionPatrocinante(TimeStampedModel):
    grupo = models.ForeignKey(GrupoScout, on_delete=models.CASCADE, related_name="instituciones_patrocinantes")
    nombre = models.CharField(max_length=160)
    tipo = models.CharField(max_length=60)
    representante_nombre = models.CharField(max_length=150)
    representante_telefono = models.CharField(max_length=30)
    representante_email = models.EmailField()
    logo = models.CharField(max_length=500, blank=True, validators=[validar_url_o_ruta_logo])
    fecha_inicio_convenio = models.DateField()
    fecha_fin_convenio = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Institucion patrocinante"
        verbose_name_plural = "Instituciones patrocinantes"

    def __str__(self) -> str:
        return self.nombre


class ConsejoGrupo(TimeStampedModel):
    grupo = models.OneToOneField(GrupoScout, on_delete=models.CASCADE, related_name="consejo")
    responsable_grupo = models.ForeignKey(
        "personas.Adulto",
        on_delete=models.PROTECT,
        related_name="consejos_de_grupo",
    )
    acta_nombramiento = models.FileField(upload_to="actas_consejo/", blank=True)

    class Meta:
        verbose_name = "Consejo de grupo"
        verbose_name_plural = "Consejos de grupo"

    def __str__(self) -> str:
        return f"Consejo {self.grupo.nombre_oficial}"


class ComiteGrupoCargo(TimeStampedModel):
    grupo = models.ForeignKey(GrupoScout, on_delete=models.CASCADE, related_name="comite_cargos")
    rol = models.CharField(max_length=20, choices=RolComite.choices)
    apoderado = models.ForeignKey("personas.Apoderado", on_delete=models.PROTECT, related_name="cargos_comite")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["grupo", "rol"], name="uq_comite_rol_por_grupo"),
        ]
        verbose_name = "Cargo de comite"
        verbose_name_plural = "Cargos de comite"

    def __str__(self) -> str:
        return f"{self.get_rol_display()} - {self.grupo.nombre_oficial}"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        tiene_beneficiario_activo = self.apoderado.relaciones_beneficiarios.filter(
            beneficiario__persona__estado="ACTIVO"
        ).exists()
        if not tiene_beneficiario_activo:
            raise ValidationError("El comite solo puede incluir apoderados de beneficiarios activos")

# Create your models here.

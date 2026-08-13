from django.db import models

from common.models import TimeStampedModel


class GradoFormacion(TimeStampedModel):
    nivel = models.CharField(max_length=60)
    especialidad = models.CharField(max_length=80)

    class Meta:
        ordering = ["nivel", "especialidad"]
        constraints = [
            models.UniqueConstraint(fields=["nivel", "especialidad"], name="uq_grado_nivel_especialidad"),
        ]
        verbose_name = "Grado de formacion"
        verbose_name_plural = "Grados de formacion"

    def __str__(self) -> str:
        return f"{self.nivel} - {self.especialidad}"


class AdultoGradoFormacion(TimeStampedModel):
    adulto = models.ForeignKey("personas.Adulto", on_delete=models.CASCADE, related_name="grados_formacion")
    grado = models.ForeignKey(GradoFormacion, on_delete=models.PROTECT, related_name="adultos")
    fecha_obtencion = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["adulto", "grado"], name="uq_adulto_grado_formacion"),
        ]
        verbose_name = "Formacion de adulto"
        verbose_name_plural = "Formaciones de adulto"

    def __str__(self) -> str:
        return f"{self.adulto.persona} - {self.grado}"

# Create your models here.

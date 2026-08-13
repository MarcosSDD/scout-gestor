from django.db import models

from common.models import TimeStampedModel


class ComposicionPermitida(models.TextChoices):
    MIXTA = "MIXTA", "Mixta"
    SOLO_HOMBRES = "SOLO_HOMBRES", "Solo hombres"
    SOLO_MUJERES = "SOLO_MUJERES", "Solo mujeres"


class Distrito(TimeStampedModel):
    nombre = models.CharField(max_length=100)
    zona = models.ForeignKey("Zona", on_delete=models.PROTECT, related_name="distritos")

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "zona"], name="uq_distrito_nombre_zona"),
        ]
        verbose_name = "Distrito"
        verbose_name_plural = "Distritos"

    def __str__(self) -> str:
        return self.nombre


class Zona(TimeStampedModel):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"

    def __str__(self) -> str:
        return self.nombre


class Rama(TimeStampedModel):
    nombre = models.CharField(max_length=60, unique=True)
    edad_minima = models.PositiveSmallIntegerField()
    edad_maxima = models.PositiveSmallIntegerField()
    composicion_permitida = models.CharField(
        max_length=20,
        choices=ComposicionPermitida.choices,
        default=ComposicionPermitida.MIXTA,
    )
    nomenclatura_subgrupos = models.CharField(max_length=40)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["edad_minima", "nombre"]
        verbose_name = "Rama"
        verbose_name_plural = "Ramas"

    def __str__(self) -> str:
        return self.nombre

    def clean(self) -> None:
        if self.edad_minima >= self.edad_maxima:
            from django.core.exceptions import ValidationError

            raise ValidationError("La edad minima debe ser menor a la edad maxima")

# Create your models here.

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona
from organizacion.models import GrupoScout, TipoGrupo
from personas.models import Adulto, Persona, RolAdulto, SexoPersona
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Unidad


class AdultoUnidadRolTests(TestCase):
    def setUp(self):
        self.zona = Zona.objects.create(nombre="Zona 1")
        self.distrito = Distrito.objects.create(nombre="Distrito 1", zona=self.zona)
        self.rama = Rama.objects.create(
            nombre="Tropa",
            edad_minima=11,
            edad_maxima=15,
            composicion_permitida=ComposicionPermitida.SOLO_HOMBRES,
            nomenclatura_subgrupos="Patrullas",
        )
        self.grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo A",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Direccin 123",
            comuna="Santiago",
        )
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=self.rama, nombre="Unidad A")

    def _crear_adulto(self, rut: str, sexo: str):
        persona = Persona.objects.create(
            rut=rut,
            nombres="Adulto",
            apellidos="Test",
            fecha_nacimiento="1990-01-01",
            sexo=sexo,
            direccion="Dir",
            telefono="123",
            email=f"{rut}@gmail.com",
        )
        return Adulto.objects.create(
            persona=persona,
            rol_principal=RolAdulto.GUIA,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )

    def test_unidad_acepta_solo_hombres(self):
        adulta = self._crear_adulto("11111111-1", SexoPersona.FEMENINO)
        asignacion = AdultoUnidadRol(unidad=self.unidad, adulto=adulta, rol=RolAdultoUnidad.ASISTENTE)
        with self.assertRaises(ValidationError):
            asignacion.full_clean()

    def test_unidad_permite_un_solo_responsable(self):
        adulto_1 = self._crear_adulto("22222222-2", SexoPersona.MASCULINO)
        adulto_2 = self._crear_adulto("33333333-3", SexoPersona.MASCULINO)
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto_1, rol=RolAdultoUnidad.RESPONSABLE)
        with self.assertRaises(IntegrityError):
            AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto_2, rol=RolAdultoUnidad.RESPONSABLE)

# Create your tests here.

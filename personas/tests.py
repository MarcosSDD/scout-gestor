from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from catalogos.models import ComposicionPermitida, Rama
from personas.models import Adulto, Apoderado, Beneficiario, Persona, RolAdulto, SexoPersona


class PersonaModelTests(TestCase):
    def test_rut_se_normaliza_y_valida(self):
        persona = Persona(
            rut="12.345.678-5",
            nombres="Ana",
            apellidos="Perez",
            fecha_nacimiento="2000-01-01",
            sexo=SexoPersona.FEMENINO,
            direccion="Calle 1",
            telefono="+56911111111",
            email="ana@example.com",
        )
        persona.full_clean()
        persona.save()
        self.assertEqual(persona.rut, "12345678-5")

    def test_rut_invalido_lanza_error(self):
        persona = Persona(
            rut="12345678-9",
            nombres="Ana",
            apellidos="Perez",
            fecha_nacimiento="2000-01-01",
            sexo=SexoPersona.FEMENINO,
            direccion="Calle 1",
            telefono="+56911111111",
            email="ana@example.com",
        )
        with self.assertRaises(ValidationError):
            persona.full_clean()


class AdultoModelTests(TestCase):
    def test_adulto_requiere_certificado_vigente(self):
        persona = Persona.objects.create(
            rut="11111111-1",
            nombres="Luis",
            apellidos="Rojas",
            fecha_nacimiento="1990-05-10",
            sexo=SexoPersona.MASCULINO,
            direccion="Calle 2",
            telefono="+56922222222",
            email="luis@example.com",
        )
        adulto = Adulto(
            persona=persona,
            rol_principal=RolAdulto.GUIA,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() - timezone.timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            adulto.full_clean()


class ApoderadoModelTests(TestCase):
    def test_apoderado_requiere_edad_minima_18(self):
        persona = Persona.objects.create(
            rut="9999999-3",
            nombres="Menor",
            apellidos="Apoderado",
            fecha_nacimiento=timezone.localdate() - timezone.timedelta(days=16 * 365),
            sexo=SexoPersona.FEMENINO,
            direccion="Calle 4",
            telefono="+56944444444",
            email="menor.apoderado@example.com",
        )
        apoderado = Apoderado(persona=persona)
        with self.assertRaises(ValidationError):
            apoderado.full_clean()

    def test_adulto_requiere_edad_minima_18(self):
        persona = Persona.objects.create(
            rut="87654321-4",
            nombres="Menor",
            apellidos="Edad",
            fecha_nacimiento=timezone.localdate() - timezone.timedelta(days=16 * 365),
            sexo=SexoPersona.MASCULINO,
            direccion="Calle 3",
            telefono="+56933333333",
            email="menor@example.com",
        )
        adulto = Adulto(
            persona=persona,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        with self.assertRaises(ValidationError):
            adulto.full_clean()

    def test_beneficiario_no_puede_registrarse_como_dirigente(self):
        persona = Persona.objects.create(
            rut="12345678-5",
            nombres="Ben",
            apellidos="Scout",
            fecha_nacimiento=timezone.datetime(2012, 1, 1).date(),
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="ben-scout@example.com",
        )
        rama = Rama.objects.create(
            nombre="Manada Test",
            edad_minima=7,
            edad_maxima=11,
            composicion_permitida=ComposicionPermitida.MIXTA,
            nomenclatura_subgrupos="Seisenas",
        )
        Beneficiario.objects.create(persona=persona, rama_actual=rama, fecha_ingreso="2024-01-01")
        adulto = Adulto(
            persona=persona,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        with self.assertRaises(ValidationError):
            adulto.full_clean()

# Create your tests here.

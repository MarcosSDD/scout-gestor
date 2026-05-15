from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from personas.models import Adulto, Persona, RolAdulto, SexoPersona


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

# Create your tests here.

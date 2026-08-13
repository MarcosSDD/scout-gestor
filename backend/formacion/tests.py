from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone

from formacion.models import AdultoGradoFormacion, GradoFormacion
from personas.models import Adulto, Persona, RolAdulto, SexoPersona


class FormacionTests(TestCase):
    def test_adulto_no_repite_mismo_grado(self):
        persona = Persona.objects.create(
            rut="12345678-5",
            nombres="Adulto",
            apellidos="Formado",
            fecha_nacimiento="1992-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="adulto@test.com",
        )
        adulto = Adulto.objects.create(
            persona=persona,
            rol_principal=RolAdulto.GUIA,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=90),
        )
        grado = GradoFormacion.objects.create(nivel="Basico", especialidad="Manada")

        AdultoGradoFormacion.objects.create(adulto=adulto, grado=grado, fecha_obtencion="2024-01-01")
        with self.assertRaises(IntegrityError):
            AdultoGradoFormacion.objects.create(adulto=adulto, grado=grado, fecha_obtencion="2024-02-01")

# Create your tests here.

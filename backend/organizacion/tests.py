from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona
from organizacion.models import ComiteGrupoCargo, GrupoScout, InstitucionPatrocinante, RolComite, TipoGrupo
from personas.models import (
    Adulto,
    Apoderado,
    ApoderadoBeneficiario,
    Beneficiario,
    Persona,
    RolAdulto,
    SexoPersona,
)
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Unidad


class GrupoScoutTests(TestCase):
    def setUp(self):
        self.zona = Zona.objects.create(nombre="Zona X")
        self.distrito = Distrito.objects.create(nombre="Distrito X", zona=self.zona)
        self.rama = Rama.objects.create(
            nombre="Manada",
            edad_minima=7,
            edad_maxima=11,
            composicion_permitida=ComposicionPermitida.MIXTA,
            nomenclatura_subgrupos="Seisenas",
        )
        self.grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo Test",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Direccion",
            comuna="Comuna",
        )
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=self.rama, nombre="Unidad 1")

    def test_recalculo_minimo_miembros_pone_observacion(self):
        persona_b = Persona.objects.create(
            rut="12345678-5",
            nombres="Nina",
            apellidos="Scout",
            fecha_nacimiento="2015-01-01",
            sexo=SexoPersona.FEMENINO,
            direccion="Dir",
            telefono="123",
            email="nina@test.com",
        )
        Beneficiario.objects.create(
            persona=persona_b,
            rama_actual=self.rama,
            unidad=self.unidad,
            fecha_ingreso="2024-03-01",
        )
        persona_a = Persona.objects.create(
            rut="11111111-1",
            nombres="Jefe",
            apellidos="Unidad",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="jefe@test.com",
        )
        adulto = Adulto.objects.create(
            persona=persona_a,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=5),
        )
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto, rol=RolAdultoUnidad.ASISTENTE)

        minimo = self.grupo.recalcular_minimo_miembros()
        self.assertEqual(minimo, 2)
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.estado_vigencia, "OBSERVACION")

    def test_grupo_valida_que_distrito_pertenezca_a_zona(self):
        otra_zona = Zona.objects.create(nombre="Zona Y")
        distrito_otra_zona = Distrito.objects.create(nombre="Distrito Y", zona=otra_zona)
        grupo = GrupoScout(
            nombre_oficial="Grupo Inconsistente",
            distrito=distrito_otra_zona,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Direccion",
            comuna="Comuna",
        )
        with self.assertRaises(ValidationError):
            grupo.full_clean()

    def test_grupo_acepta_logo_como_url_o_ruta(self):
        grupo_url = GrupoScout(
            nombre_oficial="Grupo Logo URL",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Direccion",
            comuna="Comuna",
            logo="https://cdn.scouts.cl/logos/grupo.png",
        )
        grupo_url.full_clean()

        grupo_ruta = GrupoScout(
            nombre_oficial="Grupo Logo Ruta",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Direccion",
            comuna="Comuna",
            logo="/srv/scouts/logos/grupo.png",
        )
        grupo_ruta.full_clean()

    def test_grupo_rechaza_logo_invalido(self):
        grupo = GrupoScout(
            nombre_oficial="Grupo Logo Invalido",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Direccion",
            comuna="Comuna",
            logo="ftp://scouts/logo.png",
        )
        with self.assertRaises(ValidationError):
            grupo.full_clean()


class ComiteGrupoCargoTests(TestCase):
    def setUp(self):
        zona = Zona.objects.create(nombre="Zona C")
        distrito = Distrito.objects.create(nombre="Distrito C", zona=zona)
        self.grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo Comite",
            distrito=distrito,
            zona=zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Dir",
            comuna="Comuna",
        )

    def test_comite_requiere_apoderado_de_beneficiario_activo(self):
        persona_ap = Persona.objects.create(
            rut="22222222-2",
            nombres="Apoderado",
            apellidos="Test",
            fecha_nacimiento="1985-01-01",
            sexo=SexoPersona.FEMENINO,
            direccion="Dir",
            telefono="123",
            email="ap@test.com",
        )
        apoderado = Apoderado.objects.create(persona=persona_ap)
        cargo = ComiteGrupoCargo(grupo=self.grupo, rol=RolComite.PRESIDENTE, apoderado=apoderado)
        with self.assertRaises(ValidationError):
            cargo.full_clean()

        persona_b = Persona.objects.create(
            rut="33333333-3",
            nombres="Benef",
            apellidos="Activo",
            fecha_nacimiento="2010-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="benef@test.com",
        )
        beneficiario = Beneficiario.objects.create(persona=persona_b, fecha_ingreso="2024-01-01")
        ApoderadoBeneficiario.objects.create(
            apoderado=apoderado,
            beneficiario=beneficiario,
            parentesco="PADRE",
        )
        cargo.full_clean()


class InstitucionPatrocinanteTests(TestCase):
    def test_institucion_acepta_logo_como_url_o_ruta(self):
        zona = Zona.objects.create(nombre="Zona I")
        distrito = Distrito.objects.create(nombre="Distrito I", zona=zona)
        grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo Institucion",
            distrito=distrito,
            zona=zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Dir",
            comuna="Comuna",
        )

        institucion = InstitucionPatrocinante(
            grupo=grupo,
            nombre="Colegio Scout",
            tipo="Escuela",
            representante_nombre="Maria",
            representante_telefono="123",
            representante_email="maria@test.com",
            logo="media/logos/institucion.png",
            fecha_inicio_convenio="2025-01-01",
        )
        institucion.full_clean()

# Create your tests here.

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona
from organizacion.models import GrupoScout, TipoGrupo
from personas.models import Adulto, Apoderado, AreaDesarrollo, Beneficiario, Persona, RegistroProgresionScout, RolAdulto, SexoPersona, TipoRegistroProgresion


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


class RegistroProgresionScoutModelTests(TestCase):
    def _beneficiario(self):
        persona = Persona.objects.create(
            rut="22345676-2",
            nombres="Progreso",
            apellidos="Scout",
            fecha_nacimiento=timezone.datetime(2012, 1, 1).date(),
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="progreso-scout@example.com",
        )
        rama = Rama.objects.create(
            nombre="Tropa Progresion",
            edad_minima=11,
            edad_maxima=15,
            composicion_permitida=ComposicionPermitida.MIXTA,
            nomenclatura_subgrupos="Patrullas",
        )
        return Beneficiario.objects.create(persona=persona, rama_actual=rama, fecha_ingreso=timezone.localdate())

    def test_areas_desarrollo_base_existen(self):
        codigos = set(AreaDesarrollo.objects.values_list("codigo", flat=True))
        self.assertEqual(
            codigos,
            {"CORPORALIDAD", "CREATIVIDAD", "CARACTER", "AFECTIVIDAD", "SOCIABILIDAD", "ESPIRITUALIDAD"},
        )

    def test_registro_requiere_texto(self):
        registro = RegistroProgresionScout(
            beneficiario=self._beneficiario(),
            fecha=timezone.localdate(),
            tipo=TipoRegistroProgresion.DURANTE_CICLO,
            texto="",
        )
        with self.assertRaises(ValidationError):
            registro.full_clean()

    def test_registro_no_permite_fecha_futura(self):
        registro = RegistroProgresionScout(
            beneficiario=self._beneficiario(),
            fecha=timezone.localdate() + timezone.timedelta(days=1),
            tipo=TipoRegistroProgresion.DURANTE_CICLO,
            texto="Observacion del periodo",
        )
        with self.assertRaises(ValidationError):
            registro.full_clean()


class SyncRolAdultoGuiadoraMigrationTests(TransactionTestCase):
    migrate_from = ("personas", "0006_alter_adulto_certificado_inhabilidades_and_more")
    migrate_to = ("personas", "0007_sync_rol_adulto_guiadora")

    def setUp(self):
        self.executor = MigrationExecutor(connection)
        self.latest_migration_targets = self.executor.loader.graph.leaf_nodes()
        self.executor.migrate([self.migrate_from])
        self.old_apps = self.executor.loader.project_state([self.migrate_from]).apps

    def tearDown(self):
        self.executor.loader.build_graph()
        self.executor.migrate(self.latest_migration_targets)
        super().tearDown()

    def test_regularizes_assigned_adults_and_preserves_special_roles(self):
        Rama = self.old_apps.get_model("catalogos", "Rama")
        Unidad = self.old_apps.get_model("unidades", "Unidad")
        Persona = self.old_apps.get_model("personas", "Persona")
        Adulto = self.old_apps.get_model("personas", "Adulto")
        AdultoUnidadRol = self.old_apps.get_model("unidades", "AdultoUnidadRol")

        rama = Rama.objects.create(
            nombre="Rama migracion roles",
            edad_minima=7,
            edad_maxima=18,
            composicion_permitida="MIXTA",
            nomenclatura_subgrupos="Equipos",
        )
        zona = Zona.objects.create(nombre="Zona migracion roles")
        grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo migracion roles",
            zona=zona,
            distrito=Distrito.objects.create(
                nombre="Distrito migracion roles",
                zona=zona,
            ),
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Direccion",
            comuna="Comuna",
        )
        unidad = Unidad.objects.create(grupo_id=grupo.pk, rama_id=rama.pk, nombre="Unidad migracion roles")

        def create_adulto(index, sexo, rol):
            persona = Persona.objects.create(
                rut=f"{index}1111111-1",
                nombres="Adulto",
                apellidos=str(index),
                fecha_nacimiento="1990-01-01",
                sexo=sexo,
                direccion="Direccion",
                telefono="123",
                email=f"adulto-{index}@example.test",
            )
            return Adulto.objects.create(
                persona=persona,
                rol_principal=rol,
                certificado_inhabilidades="certificados/test.pdf",
                certificado_vigencia_hasta="2099-01-01",
            )

        create_adulto(1, "F", "GUIA")
        femenina_asignada = create_adulto(2, "F", "DIRIGENTE")
        masculino_asignado = create_adulto(3, "M", "GUIA")
        otro_asignado = create_adulto(4, "OT", "GUIA")
        apoderado = create_adulto(5, "F", "APODERADO")
        responsable_grupo = create_adulto(6, "M", "RESP_GRUPO")
        colaborador = create_adulto(7, "F", "COLABORADOR")
        for adulto in (femenina_asignada, masculino_asignado, otro_asignado, apoderado, responsable_grupo, colaborador):
            AdultoUnidadRol.objects.create(unidad=unidad, adulto=adulto, rol="ASISTENTE")

        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_to])
        new_apps = self.executor.loader.project_state([self.migrate_to]).apps
        Adulto = new_apps.get_model("personas", "Adulto")

        roles = dict(Adulto.objects.values_list("persona__email", "rol_principal"))
        self.assertEqual(roles["adulto-1@example.test"], "GUIADORA")
        self.assertEqual(roles["adulto-2@example.test"], "GUIADORA")
        self.assertEqual(roles["adulto-3@example.test"], "DIRIGENTE")
        self.assertEqual(roles["adulto-4@example.test"], "GUIADORA")
        self.assertEqual(roles["adulto-5@example.test"], "APODERADO")
        self.assertEqual(roles["adulto-6@example.test"], "RESP_GRUPO")
        self.assertEqual(roles["adulto-7@example.test"], "COLABORADOR")

        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_from])
        reverted_apps = self.executor.loader.project_state([self.migrate_from]).apps
        Adulto = reverted_apps.get_model("personas", "Adulto")
        reverted_roles = dict(Adulto.objects.values_list("persona__email", "rol_principal"))
        self.assertEqual(reverted_roles["adulto-1@example.test"], "GUIA")
        self.assertEqual(reverted_roles["adulto-2@example.test"], "GUIA")
        self.assertEqual(reverted_roles["adulto-3@example.test"], "DIRIGENTE")
        self.assertEqual(reverted_roles["adulto-4@example.test"], "GUIA")
        self.assertEqual(reverted_roles["adulto-5@example.test"], "APODERADO")
        self.assertEqual(reverted_roles["adulto-6@example.test"], "RESP_GRUPO")
        self.assertEqual(reverted_roles["adulto-7@example.test"], "COLABORADOR")

# Create your tests here.

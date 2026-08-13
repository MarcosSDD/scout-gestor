import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from catalogos.models import Rama, Zona
from organizacion.models import ConsejoGrupo, GrupoScout, TipoGrupo
from organizacion.services import DEMO_GROUP_NAME, DEMO_GROUP_REFERENCE, DEMO_MARKER, DEMO_PASSWORD, DEMO_USER_EMAILS, DEMO_USERNAMES
from personas.models import Adulto, Apoderado, ApoderadoBeneficiario, Beneficiario, Parentesco, Persona, SexoPersona
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Subgrupo, SubgrupoMiembro, Unidad


class SeedGrupoDemoCommandTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_root.cleanup)

    def _seed(self):
        self._command()
        return GrupoScout.objects.get(nombre_oficial=DEMO_GROUP_NAME)

    def _command(self, *args):
        # Docker tests use PostgreSQL, while the command is intentionally restricted
        # to SQLite. The guard itself has dedicated rejection coverage below.
        with override_settings(DEBUG=True), patch("organizacion.services.connection", SimpleNamespace(vendor="sqlite")):
            call_command("seed_grupo_demo", *args)

    def _homonymous_group(self, *, reference):
        call_command("seed_catalogos")
        zona = Zona.objects.get(nombre="Zona De Los Ríos")
        distrito = zona.distritos.get(nombre="Distrito Valdivia")
        grupo = GrupoScout(
            nombre_oficial=DEMO_GROUP_NAME,
            zona=zona,
            distrito=distrito,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Calle externa 1",
            comuna="Valdivia",
            referencia=reference,
        )
        grupo.full_clean()
        grupo.save()
        return grupo

    def test_creates_complete_demo_with_rbac_invariants(self):
        grupo = self._seed()

        self.assertEqual(Unidad.objects.filter(grupo=grupo).count(), 6)
        self.assertEqual(Subgrupo.objects.filter(unidad__grupo=grupo).count(), 6)
        self.assertEqual(Beneficiario.objects.filter(unidad__grupo=grupo).count(), 18)
        self.assertEqual(Apoderado.objects.filter(relaciones_beneficiarios__beneficiario__unidad__grupo=grupo).count(), 18)
        self.assertEqual(ApoderadoBeneficiario.objects.filter(beneficiario__unidad__grupo=grupo).count(), 18)
        self.assertEqual(AdultoUnidadRol.objects.filter(unidad__grupo=grupo, rol=RolAdultoUnidad.RESPONSABLE).count(), 6)
        self.assertEqual(Adulto.objects.filter(persona__usuario__username="demo_responsable_grupo").count(), 1)
        self.assertTrue(ConsejoGrupo.objects.filter(grupo=grupo, responsable_grupo__persona__usuario__username="demo_responsable_grupo").exists())
        for subgrupo in Subgrupo.objects.filter(unidad__grupo=grupo):
            self.assertEqual(subgrupo.miembros.count(), 3)
            self.assertIsNotNone(subgrupo.lider_juvenil)
            self.assertTrue(SubgrupoMiembro.objects.filter(subgrupo=subgrupo, beneficiario=subgrupo.lider_juvenil).exists())
        self.assertEqual(grupo.minimo_miembros_calculado, 24)

        user_model = get_user_model()
        for username in DEMO_USERNAMES:
            user = user_model.objects.get(username=username)
            self.assertTrue(user.check_password(DEMO_PASSWORD))
            expected_email = DEMO_USER_EMAILS.get(username, f"{username}@demo.scout.local")
            self.assertEqual(user.email, expected_email)
            self.assertEqual(user.last_name, DEMO_MARKER)
        self.assertTrue(user_model.objects.get(username="demo_staff").is_staff)
        self.assertTrue(hasattr(user_model.objects.get(username="demo_apoderado"), "persona"))
        self.assertTrue(Apoderado.objects.filter(persona__usuario__username="demo_apoderado").exists())
        self.assertEqual(user_model.objects.filter(username__startswith="demo_apoderado").count(), 1)
        self.assertFalse(hasattr(user_model.objects.get(username="demo_sin_persona"), "persona"))
        for name in Adulto.objects.filter(persona__usuario__username__startswith="demo_responsable_").values_list(
            "certificado_inhabilidades", flat=True
        ):
            self.assertTrue(name.startswith("certificados_inhabilidades/"))
            self.assertTrue(default_storage.exists(name))

    def test_is_idempotent(self):
        self._seed()
        before = (
            Unidad.objects.count(), Subgrupo.objects.count(), Beneficiario.objects.count(),
            Apoderado.objects.count(), ApoderadoBeneficiario.objects.count(), AdultoUnidadRol.objects.count(),
        )
        self._seed()
        after = (
            Unidad.objects.count(), Subgrupo.objects.count(), Beneficiario.objects.count(),
            Apoderado.objects.count(), ApoderadoBeneficiario.objects.count(), AdultoUnidadRol.objects.count(),
        )
        self.assertEqual(before, after)

    def test_reset_removes_only_demo_files_then_recreates_demo(self):
        self._seed()
        certificate_names = list(Adulto.objects.values_list("certificado_inhabilidades", flat=True))
        with self.captureOnCommitCallbacks(execute=True):
            self._command("--reset", "--no-input")

        self.assertEqual(GrupoScout.objects.filter(nombre_oficial=DEMO_GROUP_NAME).count(), 1)
        self.assertEqual(Unidad.objects.filter(grupo__nombre_oficial=DEMO_GROUP_NAME).count(), 6)
        self.assertEqual(get_user_model().objects.filter(username__in=DEMO_USERNAMES).count(), len(DEMO_USERNAMES))
        self.assertTrue(all(not default_storage.exists(name) for name in certificate_names))

    def test_reset_aborts_when_demo_apoderado_has_external_relation(self):
        grupo = self._seed()
        demo_apoderado = Apoderado.objects.get(persona__usuario__username="demo_apoderado")
        external_persona = Persona(
            rut="12345678-5",
            nombres="Beneficiario",
            apellidos="Externo",
            fecha_nacimiento="2015-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Calle Externa 1",
            telefono="+56922222222",
            email="externo@example.test",
        )
        external_persona.full_clean()
        external_persona.save()
        external_beneficiario = Beneficiario(persona=external_persona, fecha_ingreso="2025-01-01")
        external_beneficiario.full_clean()
        external_beneficiario.save()
        relation = ApoderadoBeneficiario(
            apoderado=demo_apoderado,
            beneficiario=external_beneficiario,
            parentesco=Parentesco.PADRE,
        )
        relation.full_clean()
        relation.save()
        before = (GrupoScout.objects.count(), Beneficiario.objects.count(), ApoderadoBeneficiario.objects.count())

        with self.assertRaises(CommandError):
            self._command("--reset", "--no-input")

        self.assertTrue(GrupoScout.objects.filter(pk=grupo.pk).exists())
        self.assertEqual(
            (GrupoScout.objects.count(), Beneficiario.objects.count(), ApoderadoBeneficiario.objects.count()), before
        )
        self.assertTrue(ApoderadoBeneficiario.objects.filter(pk=relation.pk).exists())

    def test_reset_does_not_delete_unmarked_homonymous_group(self):
        grupo = self._homonymous_group(reference="Referencia externa")
        unidad = Unidad(grupo=grupo, rama=Rama.objects.get(nombre="Golondrinas"), nombre="Unidad Externa")
        unidad.full_clean()
        unidad.save()

        with self.assertRaises(CommandError):
            self._command("--reset", "--no-input")

        self.assertTrue(GrupoScout.objects.filter(pk=grupo.pk).exists())
        self.assertTrue(Unidad.objects.filter(pk=unidad.pk).exists())

    def test_reset_does_not_delete_marked_homonymous_group_with_unexpected_unit(self):
        grupo = self._homonymous_group(reference=DEMO_GROUP_REFERENCE)
        unidad = Unidad(grupo=grupo, rama=Rama.objects.get(nombre="Golondrinas"), nombre="Unidad Externa")
        unidad.full_clean()
        unidad.save()

        with self.assertRaises(CommandError):
            self._command("--reset", "--no-input")

        self.assertTrue(GrupoScout.objects.filter(pk=grupo.pk).exists())
        self.assertTrue(Unidad.objects.filter(pk=unidad.pk).exists())

    def test_reserved_non_demo_user_is_not_modified(self):
        user = get_user_model().objects.create_user(
            username="demo_staff",
            email="staff@external.example",
            password="external-password",
        )

        with self.assertRaises(CommandError):
            self._command()

        user.refresh_from_db()
        self.assertEqual(user.email, "staff@external.example")
        self.assertEqual(user.last_name, "")
        self.assertTrue(user.check_password("external-password"))
        self.assertFalse(GrupoScout.objects.filter(nombre_oficial=DEMO_GROUP_NAME).exists())

    def test_reset_requires_non_interactive_confirmation(self):
        with self.assertRaises(CommandError):
            call_command("seed_grupo_demo", "--reset")

    @override_settings(DEBUG=False)
    def test_rejects_debug_false(self):
        with self.assertRaises(CommandError):
            call_command("seed_grupo_demo")

    def test_rejects_non_sqlite_database(self):
        with patch("organizacion.services.connection", SimpleNamespace(vendor="postgresql")):
            with self.assertRaises(CommandError):
                call_command("seed_grupo_demo")

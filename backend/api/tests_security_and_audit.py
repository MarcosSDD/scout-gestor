from io import BytesIO
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from pypdf import PdfWriter
from rest_framework import status
from rest_framework.test import APITestCase

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona
from organizacion.models import ConsejoGrupo, GrupoScout, TipoGrupo
from personas.models import (
    Adulto,
    Apoderado,
    ApoderadoBeneficiario,
    AreaDesarrollo,
    Beneficiario,
    Parentesco,
    Persona,
    RegistroProgresionScout,
    RolAdulto,
    SexoPersona,
    TipoRegistroProgresion,
)
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Unidad


class SecurityAndAuditApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.media_dir = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(shutil.rmtree, self.media_dir, ignore_errors=True)

        self.staff = get_user_model().objects.create_user(
            "staff9a", email="staff9a@example.test", password="password", is_staff=True
        )
        self.guardian_user = get_user_model().objects.create_user("guardian9a", password="password")
        zona = Zona.objects.create(nombre="Zona 9A")
        distrito = Distrito.objects.create(nombre="Distrito 9A", zona=zona)
        rama = Rama.objects.create(
            nombre="Rama 9A", edad_minima=7, edad_maxima=17,
            composicion_permitida=ComposicionPermitida.MIXTA, nomenclatura_subgrupos="Patrullas",
        )
        self.grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo 9A", zona=zona, distrito=distrito,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL, direccion="Direccion", comuna="Santiago",
        )
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=rama, nombre="Unidad 9A")
        self.other_unit = Unidad.objects.create(grupo=self.grupo, rama=rama, nombre="Unidad 9A B")
        self.other_rama = Rama.objects.create(
            nombre="Rama 9A Alternativa", edad_minima=18, edad_maxima=21,
            composicion_permitida=ComposicionPermitida.MIXTA, nomenclatura_subgrupos="Equipos",
        )
        self.beneficiario_persona = Persona.objects.create(
            rut="12345678-5", nombres="Nina", apellidos="Scout", fecha_nacimiento="2012-01-01",
            sexo=SexoPersona.FEMENINO, direccion="Secreta 1", telefono="999", email="nina@example.com",
        )
        self.beneficiario = Beneficiario.objects.create(
            persona=self.beneficiario_persona, rama_actual=rama, unidad=self.unidad, fecha_ingreso="2024-01-01",
        )
        guardian_persona = Persona.objects.create(
            usuario=self.guardian_user, rut="11111111-1", nombres="Gabi", apellidos="Apoderada",
            fecha_nacimiento="1980-01-01", sexo=SexoPersona.FEMENINO, direccion="Privada", telefono="888",
            email="guardian@example.com",
        )
        guardian = Apoderado.objects.create(persona=guardian_persona)
        ApoderadoBeneficiario.objects.create(apoderado=guardian, beneficiario=self.beneficiario, parentesco=Parentesco.MADRE)
        self.unrelated_guardian_user = get_user_model().objects.create_user("guardian-other9a", password="password")
        unrelated_guardian_persona = Persona.objects.create(
            usuario=self.unrelated_guardian_user, rut="22222222-2", nombres="Otra", apellidos="Apoderada",
            fecha_nacimiento="1980-01-01", sexo=SexoPersona.FEMENINO, direccion="Privada", telefono="777",
            email="other-guardian@example.com",
        )
        Apoderado.objects.create(persona=unrelated_guardian_persona)
        self.collaborator_user = get_user_model().objects.create_user("collaborator9a", password="password")
        collaborator_persona = Persona.objects.create(
            usuario=self.collaborator_user, rut="33333333-3", nombres="Col", apellidos="Unidad",
            fecha_nacimiento="1980-01-01", sexo=SexoPersona.MASCULINO, direccion="Privada", telefono="666",
            email="collaborator@example.com",
        )
        collaborator = Adulto.objects.create(
            persona=collaborator_persona,
            rol_principal=RolAdulto.COLABORADOR,
            certificado_inhabilidades="certificados/collaborator.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=collaborator, rol=RolAdultoUnidad.COLABORADOR)
        self.area = AreaDesarrollo.objects.create(codigo="A9A", nombre="Area 9A", definicion="Definicion")
        self.registro = RegistroProgresionScout.objects.create(
            beneficiario=self.beneficiario, fecha=timezone.localdate(), tipo=TipoRegistroProgresion.INICIO_CICLO,
            texto="Registro privado",
        )
        self.registro.areas.add(self.area)

    def _authenticate(self, user):
        self.client.force_authenticate(user)

    def _valid_pdf(self, name="certificado.pdf"):
        body = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(body)
        return SimpleUploadedFile(name, body.getvalue(), content_type="application/pdf")

    def _save_beneficiario_photo(self):
        image = Image.new("RGB", (2, 2), "white")
        body = BytesIO()
        image.save(body, format="PNG")
        self.beneficiario_persona.foto.save("foto.png", ContentFile(body.getvalue()), save=True)

    def test_apoderado_no_recibe_pii_sensible_ni_progresiones(self):
        self._authenticate(self.guardian_user)
        response = self.client.get(reverse("v1:beneficiarios-detail", kwargs={"pk": self.beneficiario.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        persona = response.data["data"]["persona"]
        for field in ("rut", "direccion", "telefono", "email", "foto"):
            self.assertNotIn(field, persona)
        self.assertEqual(response.data["data"]["registros_progresion_recientes"], [])
        self.assertEqual(self.client.get(reverse("v1:progresiones-list")).data["data"], [])

    def test_patch_beneficiario_no_permite_manipular_unidad_destino(self):
        self._authenticate(self.staff)
        response = self.client.patch(
            reverse("v1:beneficiarios-detail", kwargs={"pk": self.beneficiario.pk}),
            {"unidad": self.other_unit.pk}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.beneficiario.refresh_from_db()
        self.assertEqual(self.beneficiario.unidad_id, self.unidad.pk)

    def test_patch_unidad_no_permite_modificar_rama(self):
        self._authenticate(self.staff)
        response = self.client.patch(
            reverse("v1:unidades-detail", kwargs={"pk": self.unidad.pk}),
            {"rama": self.other_rama.pk}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.unidad.refresh_from_db()
        self.assertEqual(self.unidad.rama_id, self.beneficiario.rama_actual_id)

    def test_foto_es_privada_y_se_descarga_con_headers_seguros(self):
        self._save_beneficiario_photo()
        self._authenticate(self.guardian_user)

        response = self.client.get(reverse("v1:personas-foto", kwargs={"pk": self.beneficiario_persona.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(self.client.get(f"/media/{self.beneficiario_persona.foto.name}").status_code, status.HTTP_404_NOT_FOUND)

    def test_foto_deniega_colaborador_y_apoderado_ajeno(self):
        self._save_beneficiario_photo()
        for user in (self.collaborator_user, self.unrelated_guardian_user):
            self._authenticate(user)
            response = self.client.get(reverse("v1:personas-foto", kwargs={"pk": self.beneficiario_persona.pk}))
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_responsable_grupo_puede_descargar_foto_y_certificado_del_grupo(self):
        self._save_beneficiario_photo()
        responsable = self.collaborator_user.persona.adulto
        responsable.certificado_inhabilidades.save("certificado.pdf", self._valid_pdf(), save=True)
        ConsejoGrupo.objects.create(grupo=self.grupo, responsable_grupo=responsable)
        self._authenticate(self.collaborator_user)

        foto_response = self.client.get(
            reverse("v1:personas-foto", kwargs={"pk": self.beneficiario_persona.pk})
        )
        certificado_response = self.client.get(
            reverse("v1:adultos-certificado", kwargs={"pk": responsable.pk})
        )

        self.assertEqual(foto_response.status_code, status.HTTP_200_OK)
        self.assertEqual(certificado_response.status_code, status.HTTP_200_OK)
        self.assertIn("attachment", certificado_response["Content-Disposition"])

    def test_historial_registra_usuario_en_patch_autenticado(self):
        login = self.client.post(
            reverse("v1:auth-token"), {"email": self.staff.email, "password": "password"}, format="json"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}")
        response = self.client.patch(
            reverse("v1:progresiones-detail", kwargs={"pk": self.registro.pk}),
            {"texto": "Registro actualizado"}, format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.registro.history.filter(history_user=self.staff).exists())

    def test_certificado_exige_pdf_real_y_descarga_solo_staff_o_responsable(self):
        adulto_persona = Persona.objects.create(
            rut="44444444-4", nombres="Adulto", apellidos="Seguro", fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.MASCULINO, direccion="Direccion", telefono="777", email="adulto@example.com",
        )
        self._authenticate(self.staff)
        invalid = self.client.post(
            reverse("v1:adultos-list"),
            {"persona": adulto_persona.pk, "rol_principal": RolAdulto.GUIA,
             "certificado_inhabilidades": SimpleUploadedFile("cert.pdf", b"no es pdf", content_type="application/pdf"),
             "certificado_vigencia_hasta": str(timezone.localdate() + timezone.timedelta(days=10))},
            format="multipart",
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        malformed = self.client.post(
            reverse("v1:adultos-list"),
            {"persona": adulto_persona.pk, "rol_principal": RolAdulto.GUIA,
             "certificado_inhabilidades": SimpleUploadedFile("cert.pdf", b"%PDF- bytes invalidos", content_type="application/pdf"),
             "certificado_vigencia_hasta": str(timezone.localdate() + timezone.timedelta(days=10))},
            format="multipart",
        )
        self.assertEqual(malformed.status_code, status.HTTP_400_BAD_REQUEST)
        valid = self.client.post(
            reverse("v1:adultos-list"),
            {"persona": adulto_persona.pk, "rol_principal": RolAdulto.GUIA,
             "certificado_inhabilidades": self._valid_pdf(),
             "certificado_vigencia_hasta": str(timezone.localdate() + timezone.timedelta(days=10))},
            format="multipart",
        )
        self.assertEqual(valid.status_code, status.HTTP_201_CREATED)
        adulto = Adulto.objects.get(pk=valid.data["data"]["id"])
        adulto.asignaciones_unidad.create(unidad=self.unidad, rol="ASISTENTE")
        download = self.client.get(reverse("v1:adultos-certificado", kwargs={"pk": adulto.pk}))
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertIn("attachment", download["Content-Disposition"])
        self._authenticate(self.guardian_user)
        self.assertEqual(
            self.client.get(reverse("v1:adultos-certificado", kwargs={"pk": adulto.pk})).status_code,
            status.HTTP_403_FORBIDDEN,
        )

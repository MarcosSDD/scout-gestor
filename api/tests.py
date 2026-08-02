import shutil
import tempfile
from io import BytesIO

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from PIL import Image
from pypdf import PdfWriter

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona
from formacion.models import AdultoGradoFormacion, GradoFormacion
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
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Subgrupo, Unidad


class ApiTests(APITestCase):
    def test_health_endpoint_es_publico_y_responde_formato_estandar(self):
        response = self.client.get(reverse("v1:health"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], "ok")
        self.assertEqual(response.data["data"]["version"], "v1")

    def test_endpoint_protegido_retorna_error_estandar(self):
        response = self.client.get(reverse("v1:protected-ping"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertIn("error", response.data)


class AuthApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="responsable1",
            password="testpass123",
            email="resp1@scouts.cl",
            first_name="Ana",
            last_name="Rojas",
        )

    def test_token_login_exitoso(self):
        response = self.client.post(
            reverse("v1:auth-token"),
            {"username": "responsable1", "password": "testpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["username"], "responsable1")

    def test_token_login_invalido(self):
        response = self.client.post(
            reverse("v1:auth-token"),
            {"username": "responsable1", "password": "badpass"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertIn("error", response.data)

    def test_token_refresh_exitoso(self):
        login = self.client.post(
            reverse("v1:auth-token"),
            {"username": "responsable1", "password": "testpass123"},
            format="json",
        )
        refresh = login.data["data"]["refresh"]

        response = self.client.post(reverse("v1:auth-token-refresh"), {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])

    def test_me_requiere_auth(self):
        response = self.client.get(reverse("v1:auth-me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_me_devuelve_usuario(self):
        login = self.client.post(
            reverse("v1:auth-token"),
            {"username": "responsable1", "password": "testpass123"},
            format="json",
        )
        access = login.data["data"]["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(reverse("v1:auth-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["username"], "responsable1")

    def test_logout_blacklistea_refresh(self):
        login = self.client.post(
            reverse("v1:auth-token"),
            {"username": "responsable1", "password": "testpass123"},
            format="json",
        )
        refresh = login.data["data"]["refresh"]

        logout_response = self.client.post(reverse("v1:auth-logout"), {"refresh": refresh}, format="json")
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertTrue(logout_response.data["success"])

        refresh_response = self.client.post(
            reverse("v1:auth-token-refresh"),
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(refresh_response.data["success"])

class CatalogosApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="cataloguser",
            password="testpass123",
            email="catalog@scouts.cl",
        )

        self.zona_metropolitana, _ = Zona.objects.get_or_create(nombre="Zona Metropolitana")
        self.zona_norte, _ = Zona.objects.get_or_create(nombre="Zona Norte Test")

        self.distrito_santiago, _ = Distrito.objects.get_or_create(
            nombre="Distrito Santiago",
            zona=self.zona_metropolitana,
        )
        self.distrito_huelen, _ = Distrito.objects.get_or_create(
            nombre="Distrito Huelen",
            zona=self.zona_metropolitana,
        )
        self.distrito_arica, _ = Distrito.objects.get_or_create(
            nombre="Distrito Arica Test",
            zona=self.zona_norte,
        )

        Rama.objects.update_or_create(
            nombre="Manada",
            defaults={
                "edad_minima": 7,
                "edad_maxima": 11,
                "composicion_permitida": ComposicionPermitida.MIXTA,
                "nomenclatura_subgrupos": "Seisenas",
                "activa": True,
            },
        )
        Rama.objects.update_or_create(
            nombre="Rama Inactiva",
            defaults={
                "edad_minima": 21,
                "edad_maxima": 25,
                "composicion_permitida": ComposicionPermitida.MIXTA,
                "nomenclatura_subgrupos": "Equipos",
                "activa": False,
            },
        )

    def _authenticate(self):
        login = self.client.post(
            reverse("v1:auth-token"),
            {"username": "cataloguser", "password": "testpass123"},
            format="json",
        )
        access = login.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_catalogos_requiere_autenticacion(self):
        response = self.client.get(reverse("v1:catalogos-zonas"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_zonas_lista_con_formato_estandar_y_meta(self):
        self._authenticate()
        response = self.client.get(reverse("v1:catalogos-zonas"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("data", response.data)
        self.assertIn("meta", response.data)
        self.assertGreaterEqual(response.data["meta"]["count"], 2)

    def test_distritos_filtra_por_zona(self):
        self._authenticate()
        response = self.client.get(
            reverse("v1:catalogos-distritos"),
            {"zona_id": self.zona_metropolitana.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        nombres = {item["nombre"] for item in response.data["data"]}
        self.assertEqual(nombres, {"Distrito Santiago", "Distrito Huelen"})

    def test_ramas_filtra_activa_true(self):
        self._authenticate()
        response = self.client.get(reverse("v1:catalogos-ramas"), {"activa": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["nombre"], "Manada")

    def test_catalogos_busqueda_por_nombre(self):
        self._authenticate()
        response = self.client.get(reverse("v1:catalogos-zonas"), {"search": "metro"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["nombre"], "Zona Metropolitana")


class GrupoScoutApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="grupouser",
            password="testpass123",
            email="grupos@scouts.cl",
            is_staff=True,
        )
        Persona.objects.create(
            usuario=self.user,
            rut="11.111.110-7",
            nombres="Grupo",
            apellidos="Tester",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="grupos@scouts.cl",
        )
        self.zona_centro, _ = Zona.objects.get_or_create(nombre="Zona Centro API")
        self.zona_sur, _ = Zona.objects.get_or_create(nombre="Zona Sur API")
        self.distrito_centro, _ = Distrito.objects.get_or_create(nombre="Distrito Centro API", zona=self.zona_centro)
        self.distrito_sur, _ = Distrito.objects.get_or_create(nombre="Distrito Sur API", zona=self.zona_sur)

    def _authenticate(self):
        login = self.client.post(
            reverse("v1:auth-token"),
            {"username": "grupouser", "password": "testpass123"},
            format="json",
        )
        access = login.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _grupo_payload(self, **kwargs):
        payload = {
            "nombre_oficial": "Grupo Scout API",
            "zona": self.zona_centro.id,
            "distrito": self.distrito_centro.id,
            "tipo_grupo": TipoGrupo.PLURICONFESIONAL,
            "religion": "",
            "estado_vigencia": "ACTIVO",
            "direccion": "Calle Principal 123",
            "comuna": "Santiago",
            "referencia": "Frente a plaza",
            "logo": "https://cdn.scouts.cl/logos/grupo-api.png",
        }
        payload.update(kwargs)
        return payload

    def _grupo_model_kwargs(self, **kwargs):
        payload = self._grupo_payload(**kwargs)
        payload["zona"] = Zona.objects.get(pk=payload["zona"])
        payload["distrito"] = Distrito.objects.get(pk=payload["distrito"])
        return payload

    def test_grupos_requiere_autenticacion(self):
        response = self.client.get(reverse("v1:grupos-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_grupo_create_exitoso(self):
        self._authenticate()
        response = self.client.post(reverse("v1:grupos-list"), self._grupo_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["nombre_oficial"], "Grupo Scout API")

    def test_grupo_create_falla_por_distrito_fuera_de_zona(self):
        self._authenticate()
        payload = self._grupo_payload(distrito=self.distrito_sur.id)
        response = self.client.post(reverse("v1:grupos-list"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("distrito", str(response.data["error"]["details"]).lower())

    def test_grupo_create_confesional_sin_religion(self):
        self._authenticate()
        payload = self._grupo_payload(tipo_grupo=TipoGrupo.CONFESIONAL, religion="")
        response = self.client.post(reverse("v1:grupos-list"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("religion", str(response.data["error"]["details"]).lower())

    def test_grupo_patch_actualiza_logo(self):
        self._authenticate()
        grupo = GrupoScout.objects.create(**self._grupo_model_kwargs(nombre_oficial="Grupo Patch API"))

        response = self.client.patch(
            reverse("v1:grupos-detail", kwargs={"pk": grupo.id}),
            {"logo": "/srv/scouts/logos/grupo-patch.png"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["logo"], "/srv/scouts/logos/grupo-patch.png")

    def test_grupos_lista_filtra_por_zona_y_search(self):
        self._authenticate()
        GrupoScout.objects.create(**self._grupo_model_kwargs(nombre_oficial="Grupo Centro", logo=""))
        GrupoScout.objects.create(
            **self._grupo_model_kwargs(
                nombre_oficial="Grupo Sur",
                zona=self.zona_sur.id,
                distrito=self.distrito_sur.id,
                logo="",
            )
        )

        response = self.client.get(reverse("v1:grupos-list"), {"zona_id": self.zona_centro.id, "search": "Centro"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["nombre_oficial"], "Grupo Centro")
        self.assertIn("total_beneficiarios_activos", response.data["data"][0])
        self.assertIn("total_adultos_activos", response.data["data"][0])

    def test_grupo_calcular_minimo(self):
        self._authenticate()
        rama, _ = Rama.objects.get_or_create(
            nombre="Manada API",
            defaults={
                "edad_minima": 7,
                "edad_maxima": 11,
                "composicion_permitida": ComposicionPermitida.MIXTA,
                "nomenclatura_subgrupos": "Seisenas",
                "activa": True,
            },
        )
        grupo = GrupoScout.objects.create(**self._grupo_model_kwargs(nombre_oficial="Grupo Minimo API", logo=""))
        unidad = Unidad.objects.create(grupo=grupo, rama=rama, nombre="Unidad API")

        persona_b = Persona.objects.create(
            rut="44444444-4",
            nombres="Ben",
            apellidos="Scout",
            fecha_nacimiento="2014-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="ben@scouts.cl",
        )
        Beneficiario.objects.create(persona=persona_b, rama_actual=rama, unidad=unidad, fecha_ingreso="2024-01-01")

        persona_a = Persona.objects.create(
            rut="55555555-5",
            nombres="Adulto",
            apellidos="Scout",
            fecha_nacimiento="1985-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="adulto@scouts.cl",
        )
        adulto = Adulto.objects.create(
            persona=persona_a,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        AdultoUnidadRol.objects.create(unidad=unidad, adulto=adulto, rol=RolAdultoUnidad.ASISTENTE)

        response = self.client.post(reverse("v1:grupos-calcular-minimo", kwargs={"pk": grupo.id}), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["minimo_miembros_calculado"], 2)
        self.assertEqual(response.data["data"]["estado_vigencia"], "OBSERVACION")


class PersonasUnidadesApiTests(APITestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()
        self.addCleanup(self.override_media.disable)
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

        self.user = get_user_model().objects.create_user(
            username="stage4user",
            password="testpass123",
            email="stage4@scouts.cl",
            is_staff=True,
        )
        Persona.objects.create(
            usuario=self.user,
            rut="11.111.112-3",
            nombres="Stage4",
            apellidos="Tester",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="stage4@scouts.cl",
        )
        self.zona, _ = Zona.objects.get_or_create(nombre="Zona Stage 4")
        self.distrito, _ = Distrito.objects.get_or_create(nombre="Distrito Stage 4", zona=self.zona)
        self.rama, _ = Rama.objects.get_or_create(
            nombre="Tropa Stage 4",
            defaults={
                "edad_minima": 11,
                "edad_maxima": 15,
                "composicion_permitida": ComposicionPermitida.SOLO_HOMBRES,
                "nomenclatura_subgrupos": "Patrullas",
                "activa": True,
            },
        )
        self.grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo Stage 4",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Dir 123",
            comuna="Santiago",
            logo="",
        )
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=self.rama, nombre="Unidad Stage 4")

    def _authenticate(self):
        login = self.client.post(
            reverse("v1:auth-token"),
            {"username": "stage4user", "password": "testpass123"},
            format="json",
        )
        access = login.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _persona_payload(self, **kwargs):
        payload = {
            "rut": "12.345.678-5",
            "nombres": "Persona",
            "apellidos": "Stage4",
            "fecha_nacimiento": "2000-01-01",
            "sexo": SexoPersona.MASCULINO,
            "direccion": "Calle 100",
            "telefono": "+56911111111",
            "email": "persona.stage4@scouts.cl",
            "estado": "ACTIVO",
        }
        payload.update(kwargs)
        return payload

    def _foto_png(self, name="foto.png"):
        image = Image.new("RGB", (1, 1), color="white")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()
        return SimpleUploadedFile(name, png_bytes, content_type="image/png")

    def _certificado_pdf(self, name="certificado.pdf"):
        buffer = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(buffer)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="application/pdf")

    def test_personas_y_unidades_requieren_autenticacion(self):
        personas_response = self.client.get(reverse("v1:personas-list"))
        unidades_response = self.client.get(reverse("v1:unidades-list"))

        self.assertEqual(personas_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unidades_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_debug_sirve_solo_fotos_publicas_y_no_certificados(self):
        response = self.client.get("/media/certificados_inhabilidades/test.pdf")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_validar_rut_normaliza_y_confirma(self):
        self._authenticate()

        response = self.client.post(reverse("v1:personas-validar-rut"), {"rut": "12.345.678-5"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["rut"], "12345678-5")
        self.assertTrue(response.data["data"]["valido"])

    def test_persona_create_y_patch(self):
        self._authenticate()

        create_response = self.client.post(reverse("v1:personas-list"), self._persona_payload(), format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        persona_id = create_response.data["data"]["id"]
        self.assertEqual(create_response.data["data"]["rut"], "12345678-5")

        patch_response = self.client.patch(
            reverse("v1:personas-detail", kwargs={"pk": persona_id}),
            {"estado": "INACTIVO"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["data"]["estado"], "INACTIVO")

    def test_persona_create_con_foto(self):
        self._authenticate()
        payload = self._persona_payload(foto=self._foto_png())

        response = self.client.post(reverse("v1:personas-list"), payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertNotIn("foto", response.data["data"])
        self.assertTrue(response.data["data"]["foto_disponible"])

    def test_persona_patch_actualiza_foto(self):
        self._authenticate()
        create_response = self.client.post(reverse("v1:personas-list"), self._persona_payload(), format="json")
        persona_id = create_response.data["data"]["id"]

        response = self.client.patch(
            reverse("v1:personas-detail", kwargs={"pk": persona_id}),
            {"foto": self._foto_png("foto-actualizada.png")},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("foto", response.data["data"])
        self.assertTrue(response.data["data"]["foto_disponible"])

    def test_persona_foto_rechaza_extension_no_permitida(self):
        self._authenticate()
        archivo = SimpleUploadedFile("foto.txt", b"no-es-imagen", content_type="text/plain")
        payload = self._persona_payload(foto=archivo)

        response = self.client.post(reverse("v1:personas-list"), payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("foto", str(response.data["error"]["details"]).lower())

    def test_adulto_create_falla_si_certificado_vencido(self):
        self._authenticate()
        persona_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="11.111.111-1", email="adulto.stage4@scouts.cl"),
            format="json",
        )
        persona_id = persona_response.data["data"]["id"]

        response = self.client.post(
            reverse("v1:adultos-list"),
            {
                "persona": persona_id,
                "rol_principal": RolAdulto.DIRIGENTE,
                "certificado_inhabilidades": self._certificado_pdf(),
                "certificado_vigencia_hasta": str(timezone.localdate() - timezone.timedelta(days=1)),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("certificado_vigencia_hasta", str(response.data["error"]["details"]))

    def test_apoderado_beneficiario_valida_fecha_autorizacion(self):
        self._authenticate()

        persona_benef_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="22.222.222-2", email="benef.stage4@scouts.cl"),
            format="json",
        )
        persona_benef_id = persona_benef_response.data["data"]["id"]
        beneficiario_response = self.client.post(
            reverse("v1:beneficiarios-list"),
            {
                "persona": persona_benef_id,
                "rama_actual": self.rama.id,
                "unidad": self.unidad.id,
                "fecha_ingreso": "2024-01-01",
            },
            format="json",
        )
        beneficiario_id = beneficiario_response.data["data"]["id"]

        persona_apod_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="33.333.333-3", email="apod.stage4@scouts.cl", sexo=SexoPersona.FEMENINO),
            format="json",
        )
        persona_apod_id = persona_apod_response.data["data"]["id"]
        apoderado_response = self.client.post(
            reverse("v1:apoderados-list"),
            {
                "persona": persona_apod_id,
                "es_miembro_comite": False,
                "rol_comite": "",
            },
            format="json",
        )
        apoderado_id = apoderado_response.data["data"]["id"]

        response = self.client.post(
            reverse("v1:apoderados-beneficiarios-list"),
            {
                "apoderado": apoderado_id,
                "beneficiario": beneficiario_id,
                "parentesco": Parentesco.MADRE,
                "autoriza_salidas_terreno": True,
                "fecha_autorizacion": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("fecha_autorizacion", str(response.data["error"]["details"]))

    def test_areas_desarrollo_lista_catalogo_base(self):
        self._authenticate()

        response = self.client.get(reverse("v1:areas-desarrollo-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codigos = {item["codigo"] for item in response.data["data"]}
        self.assertEqual(
            codigos,
            {"CORPORALIDAD", "CREATIVIDAD", "CARACTER", "AFECTIVIDAD", "SOCIABILIDAD", "ESPIRITUALIDAD"},
        )

    def test_progresion_create_y_filtra_por_beneficiario_area_y_tipo(self):
        self._authenticate()
        persona_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="99.999.999-9", email="progresion.stage4@scouts.cl"),
            format="json",
        )
        beneficiario_response = self.client.post(
            reverse("v1:beneficiarios-list"),
            {
                "persona": persona_response.data["data"]["id"],
                "rama_actual": self.rama.id,
                "unidad": self.unidad.id,
                "fecha_ingreso": "2024-01-01",
            },
            format="json",
        )
        beneficiario_id = beneficiario_response.data["data"]["id"]
        area = AreaDesarrollo.objects.get(codigo="CREATIVIDAD")

        create_response = self.client.post(
            reverse("v1:progresiones-list"),
            {
                "beneficiario": beneficiario_id,
                "fecha": str(timezone.localdate()),
                "tipo": TipoRegistroProgresion.DURANTE_CICLO,
                "texto": "Participa proponiendo soluciones nuevas.",
                "areas": [area.id],
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["data"]["areas"][0]["codigo"], "CREATIVIDAD")

        list_response = self.client.get(
            reverse("v1:progresiones-list"),
            {"beneficiario_id": beneficiario_id, "area_id": area.id, "tipo": TipoRegistroProgresion.DURANTE_CICLO},
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["data"]), 1)

    def test_progresion_requiere_area_y_no_permite_fecha_futura(self):
        self._authenticate()
        persona_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="10.000.005-9", email="progresion-error.stage4@scouts.cl"),
            format="json",
        )
        beneficiario_response = self.client.post(
            reverse("v1:beneficiarios-list"),
            {
                "persona": persona_response.data["data"]["id"],
                "rama_actual": self.rama.id,
                "unidad": self.unidad.id,
                "fecha_ingreso": "2024-01-01",
            },
            format="json",
        )
        beneficiario_id = beneficiario_response.data["data"]["id"]

        sin_area_response = self.client.post(
            reverse("v1:progresiones-list"),
            {
                "beneficiario": beneficiario_id,
                "fecha": str(timezone.localdate()),
                "tipo": TipoRegistroProgresion.INICIO_CICLO,
                "texto": "Inicio de ciclo.",
                "areas": [],
            },
            format="json",
        )
        self.assertEqual(sin_area_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("areas", str(sin_area_response.data["error"]["details"]))

        area = AreaDesarrollo.objects.get(codigo="CARACTER")
        fecha_futura_response = self.client.post(
            reverse("v1:progresiones-list"),
            {
                "beneficiario": beneficiario_id,
                "fecha": str(timezone.localdate() + timezone.timedelta(days=1)),
                "tipo": TipoRegistroProgresion.INICIO_CICLO,
                "texto": "Inicio de ciclo.",
                "areas": [area.id],
            },
            format="json",
        )
        self.assertEqual(fecha_futura_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha", str(fecha_futura_response.data["error"]["details"]))

    def test_unidades_adulto_rol_respeta_regla_composicion(self):
        self._authenticate()

        persona_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="44.444.444-4", email="adulta.stage4@scouts.cl", sexo=SexoPersona.FEMENINO),
            format="json",
        )
        persona_id = persona_response.data["data"]["id"]

        adulto_response = self.client.post(
            reverse("v1:adultos-list"),
            {
                "persona": persona_id,
                "rol_principal": RolAdulto.GUIA,
                "certificado_inhabilidades": self._certificado_pdf(),
                "certificado_vigencia_hasta": str(timezone.localdate() + timezone.timedelta(days=30)),
            },
            format="multipart",
        )
        adulto_id = adulto_response.data["data"]["id"]

        response = self.client.post(
            reverse("v1:unidades-adultos-roles-list"),
            {
                "unidad": self.unidad.id,
                "adulto": adulto_id,
                "rol": RolAdultoUnidad.ASISTENTE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_subgrupo_y_miembro_crud_base(self):
        self._authenticate()

        persona_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="55.555.555-5", email="subgrupo.stage4@scouts.cl"),
            format="json",
        )
        persona_id = persona_response.data["data"]["id"]
        beneficiario_response = self.client.post(
            reverse("v1:beneficiarios-list"),
            {
                "persona": persona_id,
                "rama_actual": self.rama.id,
                "unidad": self.unidad.id,
                "fecha_ingreso": "2024-01-01",
            },
            format="json",
        )
        beneficiario_id = beneficiario_response.data["data"]["id"]

        subgrupo_response = self.client.post(
            reverse("v1:subgrupos-list"),
            {"nombre": "Patrulla Roja", "unidad": self.unidad.id, "lider_juvenil": beneficiario_id},
            format="json",
        )
        self.assertEqual(subgrupo_response.status_code, status.HTTP_201_CREATED)
        subgrupo_id = subgrupo_response.data["data"]["id"]

        miembro_response = self.client.post(
            reverse("v1:subgrupos-miembros-list"),
            {"subgrupo": subgrupo_id, "beneficiario": beneficiario_id},
            format="json",
        )
        self.assertEqual(miembro_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(miembro_response.data["success"])

        listado_response = self.client.get(reverse("v1:subgrupos-miembros-list"), {"subgrupo_id": subgrupo_id})
        self.assertEqual(listado_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listado_response.data["data"]), 1)
        self.assertEqual(listado_response.data["data"][0]["beneficiario"], beneficiario_id)

    def test_beneficiario_no_puede_crearse_como_adulto_dirigente(self):
        self._authenticate()

        persona_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="66.666.666-6", email="ben-dirigente@scouts.cl", fecha_nacimiento="2000-01-01"),
            format="json",
        )
        persona_id = persona_response.data["data"]["id"]

        self.client.post(
            reverse("v1:beneficiarios-list"),
            {
                "persona": persona_id,
                "rama_actual": self.rama.id,
                "unidad": self.unidad.id,
                "fecha_ingreso": "2024-01-01",
            },
            format="json",
        )

        adulto_response = self.client.post(
            reverse("v1:adultos-list"),
            {
                "persona": persona_id,
                "rol_principal": RolAdulto.DIRIGENTE,
                "certificado_inhabilidades": self._certificado_pdf(),
                "certificado_vigencia_hasta": str(timezone.localdate() + timezone.timedelta(days=30)),
            },
            format="multipart",
        )

        self.assertEqual(adulto_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("persona", str(adulto_response.data["error"]["details"]))

    def test_adulto_con_rol_apoderado_crea_apoderado_automaticamente(self):
        self._authenticate()

        persona_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="77.777.777-7", email="adulto-apoderado@scouts.cl", sexo=SexoPersona.FEMENINO),
            format="json",
        )
        persona_id = persona_response.data["data"]["id"]

        adulto_response = self.client.post(
            reverse("v1:adultos-list"),
            {
                "persona": persona_id,
                "rol_principal": RolAdulto.APODERADO,
                "certificado_inhabilidades": self._certificado_pdf(),
                "certificado_vigencia_hasta": str(timezone.localdate() + timezone.timedelta(days=30)),
            },
            format="multipart",
        )

        self.assertEqual(adulto_response.status_code, status.HTTP_201_CREATED)

        apoderados_response = self.client.get(reverse("v1:apoderados-list"))
        self.assertEqual(apoderados_response.status_code, status.HTTP_200_OK)
        persona_ids = {item["persona"] for item in apoderados_response.data["data"]}
        self.assertIn(persona_id, persona_ids)

    def test_actualizar_adulto_a_rol_apoderado_lo_agrega_a_listado_apoderados(self):
        self._authenticate()

        persona_response = self.client.post(
            reverse("v1:personas-list"),
            self._persona_payload(rut="88.888.888-8", email="adulto-update-apoderado@scouts.cl"),
            format="json",
        )
        persona_id = persona_response.data["data"]["id"]

        adulto_response = self.client.post(
            reverse("v1:adultos-list"),
            {
                "persona": persona_id,
                "rol_principal": RolAdulto.DIRIGENTE,
                "certificado_inhabilidades": self._certificado_pdf(),
                "certificado_vigencia_hasta": str(timezone.localdate() + timezone.timedelta(days=30)),
            },
            format="multipart",
        )
        adulto_id = adulto_response.data["data"]["id"]

        patch_response = self.client.patch(
            reverse("v1:adultos-detail", kwargs={"pk": adulto_id}),
            {"rol_principal": RolAdulto.APODERADO},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        apoderados_response = self.client.get(reverse("v1:apoderados-list"))
        self.assertEqual(apoderados_response.status_code, status.HTTP_200_OK)
        persona_ids = {item["persona"] for item in apoderados_response.data["data"]}
        self.assertIn(persona_id, persona_ids)


class EstructuraJerarquiaApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="stage5user",
            password="testpass123",
            email="stage5@scouts.cl",
            is_staff=True,
        )
        Persona.objects.create(
            usuario=self.user,
            rut="11.111.113-1",
            nombres="Stage5",
            apellidos="Tester",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="123",
            email="stage5@scouts.cl",
        )

        self.zona = Zona.objects.create(nombre="Zona Stage 5")
        self.distrito = Distrito.objects.create(nombre="Distrito Stage 5", zona=self.zona)
        self.rama_tropa = Rama.objects.create(
            nombre="Tropa Stage 5",
            edad_minima=11,
            edad_maxima=15,
            composicion_permitida=ComposicionPermitida.SOLO_HOMBRES,
            nomenclatura_subgrupos="Patrullas",
            activa=True,
        )
        self.grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo Stage 5",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Dir 555",
            comuna="Santiago",
            logo="",
        )
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=self.rama_tropa, nombre="Unidad Stage 5")
        self.unidad_2 = Unidad.objects.create(grupo=self.grupo, rama=self.rama_tropa, nombre="Unidad Stage 5 B")

    def _authenticate(self):
        login = self.client.post(
            reverse("v1:auth-token"),
            {"username": "stage5user", "password": "testpass123"},
            format="json",
        )
        access = login.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _crear_persona(self, *, rut, nombres, sexo, fecha_nacimiento, email):
        return Persona.objects.create(
            rut=rut,
            nombres=nombres,
            apellidos="Stage5",
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexo,
            direccion="Dir",
            telefono="123",
            email=email,
        )

    def test_estructura_requiere_autenticacion(self):
        response = self.client.get(reverse("v1:grupos-estructura", kwargs={"pk": self.grupo.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_beneficiario_falla_si_rama_no_coincide_con_unidad(self):
        self._authenticate()
        rama_otra = Rama.objects.create(
            nombre="Clan Stage 5",
            edad_minima=17,
            edad_maxima=21,
            composicion_permitida=ComposicionPermitida.MIXTA,
            nomenclatura_subgrupos="Equipos",
            activa=True,
        )
        persona = self._crear_persona(
            rut="66.666.666-6",
            nombres="BenRama",
            sexo=SexoPersona.MASCULINO,
            fecha_nacimiento="2012-01-01",
            email="benrama@scouts.cl",
        )

        response = self.client.post(
            reverse("v1:beneficiarios-list"),
            {
                "persona": persona.id,
                "rama_actual": rama_otra.id,
                "unidad": self.unidad.id,
                "fecha_ingreso": "2024-01-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rama_actual", str(response.data["error"]["details"]))

    def test_beneficiario_falla_por_composicion_unidad(self):
        self._authenticate()
        persona = self._crear_persona(
            rut="77.777.777-7",
            nombres="BenComposicion",
            sexo=SexoPersona.FEMENINO,
            fecha_nacimiento="2012-01-01",
            email="bencomposicion@scouts.cl",
        )

        response = self.client.post(
            reverse("v1:beneficiarios-list"),
            {
                "persona": persona.id,
                "rama_actual": self.rama_tropa.id,
                "unidad": self.unidad.id,
                "fecha_ingreso": "2024-01-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("persona", str(response.data["error"]["details"]))

    def test_subgrupo_falla_si_lider_no_pertenece_a_unidad(self):
        self._authenticate()
        persona = self._crear_persona(
            rut="88.888.888-8",
            nombres="BenLider",
            sexo=SexoPersona.MASCULINO,
            fecha_nacimiento="2012-01-01",
            email="benlider@scouts.cl",
        )
        beneficiario = Beneficiario.objects.create(
            persona=persona,
            rama_actual=self.rama_tropa,
            unidad=self.unidad_2,
            fecha_ingreso="2024-01-01",
        )

        response = self.client.post(
            reverse("v1:subgrupos-list"),
            {
                "nombre": "Patrulla Error",
                "unidad": self.unidad.id,
                "lider_juvenil": beneficiario.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lider_juvenil", str(response.data["error"]["details"]))

    def test_subgrupo_miembro_falla_si_beneficiario_no_pertenece_unidad(self):
        self._authenticate()
        persona_ok = self._crear_persona(
            rut="11.111.111-1",
            nombres="BenOk",
            sexo=SexoPersona.MASCULINO,
            fecha_nacimiento="2012-01-01",
            email="benok@scouts.cl",
        )
        benef_ok = Beneficiario.objects.create(
            persona=persona_ok,
            rama_actual=self.rama_tropa,
            unidad=self.unidad,
            fecha_ingreso="2024-01-01",
        )
        subgrupo = Subgrupo.objects.create(nombre="Patrulla Azul", unidad=self.unidad, lider_juvenil=benef_ok)

        persona_otro = self._crear_persona(
            rut="22.222.222-2",
            nombres="BenOtro",
            sexo=SexoPersona.MASCULINO,
            fecha_nacimiento="2012-01-01",
            email="benotro@scouts.cl",
        )
        benef_otro = Beneficiario.objects.create(
            persona=persona_otro,
            rama_actual=self.rama_tropa,
            unidad=self.unidad_2,
            fecha_ingreso="2024-01-01",
        )

        response = self.client.post(
            reverse("v1:subgrupos-miembros-list"),
            {
                "subgrupo": subgrupo.id,
                "beneficiario": benef_otro.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("beneficiario", str(response.data["error"]["details"]))

    def test_subgrupo_miembro_falla_si_ya_esta_en_otro_subgrupo_misma_unidad(self):
        self._authenticate()
        persona = self._crear_persona(
            rut="33.333.333-3",
            nombres="BenDuplicado",
            sexo=SexoPersona.MASCULINO,
            fecha_nacimiento="2012-01-01",
            email="benduplicado@scouts.cl",
        )
        benef = Beneficiario.objects.create(
            persona=persona,
            rama_actual=self.rama_tropa,
            unidad=self.unidad,
            fecha_ingreso="2024-01-01",
        )
        subgrupo_a = Subgrupo.objects.create(nombre="Patrulla A", unidad=self.unidad, lider_juvenil=benef)
        subgrupo_b = Subgrupo.objects.create(nombre="Patrulla B", unidad=self.unidad)
        self.client.post(
            reverse("v1:subgrupos-miembros-list"),
            {"subgrupo": subgrupo_a.id, "beneficiario": benef.id},
            format="json",
        )

        response = self.client.post(
            reverse("v1:subgrupos-miembros-list"),
            {"subgrupo": subgrupo_b.id, "beneficiario": benef.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("beneficiario", str(response.data["error"]["details"]))

    def test_estructura_devuelve_arbol_y_alerta_etaria_rn05(self):
        self._authenticate()

        persona_ben = self._crear_persona(
            rut="44.444.444-4",
            nombres="BenAlerta",
            sexo=SexoPersona.MASCULINO,
            fecha_nacimiento="2005-01-01",
            email="benalerta@scouts.cl",
        )
        beneficiario = Beneficiario.objects.create(
            persona=persona_ben,
            rama_actual=self.rama_tropa,
            unidad=self.unidad,
            fecha_ingreso="2024-01-01",
        )

        persona_adulto = self._crear_persona(
            rut="55.555.555-5",
            nombres="AdultoTree",
            sexo=SexoPersona.MASCULINO,
            fecha_nacimiento="1988-01-01",
            email="adultotree@scouts.cl",
        )
        adulto = Adulto.objects.create(
            persona=persona_adulto,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto, rol=RolAdultoUnidad.ASISTENTE)
        subgrupo = Subgrupo.objects.create(nombre="Patrulla Tree", unidad=self.unidad, lider_juvenil=beneficiario)
        self.client.post(
            reverse("v1:subgrupos-miembros-list"),
            {"subgrupo": subgrupo.id, "beneficiario": beneficiario.id},
            format="json",
        )

        response = self.client.get(reverse("v1:grupos-estructura", kwargs={"pk": self.grupo.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["id"], self.grupo.id)
        self.assertGreaterEqual(response.data["data"]["resumen"]["total_unidades"], 2)
        self.assertEqual(response.data["data"]["resumen"]["total_beneficiarios"], 1)
        self.assertEqual(response.data["data"]["resumen"]["total_adultos"], 1)
        self.assertEqual(response.data["data"]["resumen"]["total_subgrupos"], 1)
        self.assertEqual(response.data["data"]["resumen"]["total_alertas_etarias"], 1)

        ramas = response.data["data"]["ramas"]
        self.assertGreaterEqual(len(ramas), 1)
        unidad_payload = ramas[0]["unidades"][0]
        self.assertIn("beneficiarios", unidad_payload)
        self.assertEqual(unidad_payload["beneficiarios"][0]["alertas"][0]["code"], "EDAD_FUERA_DE_RANGO")


class DashboardApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="stage6user",
            password="testpass123",
            email="stage6@scouts.cl",
        )
        self.zona = Zona.objects.create(nombre="Zona Stage 6")
        self.distrito = Distrito.objects.create(nombre="Distrito Stage 6", zona=self.zona)
        self.rama = Rama.objects.create(
            nombre="Rama Stage 6",
            edad_minima=11,
            edad_maxima=15,
            composicion_permitida=ComposicionPermitida.MIXTA,
            nomenclatura_subgrupos="Patrullas",
            activa=True,
        )
        self.grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo Stage 6",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Dir 666",
            comuna="Santiago",
            logo="",
        )
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=self.rama, nombre="Unidad Stage 6")
        persona_user = Persona.objects.create(
            usuario=self.user,
            rut="10.999.999-5",
            nombres="Usuario",
            apellidos="Dashboard",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="999",
            email="stage6@scouts.cl",
        )
        adulto_user = Adulto.objects.create(
            persona=persona_user,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto_user, rol=RolAdultoUnidad.COLABORADOR)

    def _authenticate(self):
        login = self.client.post(
            reverse("v1:auth-token"),
            {"username": "stage6user", "password": "testpass123"},
            format="json",
        )
        access = login.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _crear_persona(self, *, rut, nombres, apellidos, fecha_nacimiento, sexo=SexoPersona.MASCULINO, estado="ACTIVO"):
        return Persona.objects.create(
            rut=rut,
            nombres=nombres,
            apellidos=apellidos,
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexo,
            direccion="Dir",
            telefono="123",
            email=f"{rut.replace('.', '').replace('-', '')}@scouts.cl",
            estado=estado,
        )

    def test_dashboard_requiere_autenticacion(self):
        response = self.client.get(reverse("v1:dashboard-grupo", kwargs={"pk": self.grupo.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_grupo_vacio_devuelve_kpis_en_cero(self):
        self._authenticate()
        response = self.client.get(reverse("v1:dashboard-grupo", kwargs={"pk": self.grupo.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["kpis"]["total_miembros"], 1)
        self.assertEqual(response.data["data"]["kpis"]["total_adultos_activos"], 1)
        self.assertEqual(response.data["data"]["kpis"]["porcentaje_adultos_con_formacion"], 0.0)
        self.assertEqual(response.data["data"]["kpis"]["porcentaje_beneficiarios_con_apoderado_activo"], 0.0)
        self.assertEqual(response.data["data"]["alertas"]["cumpleanos_semana"], [])

    def test_dashboard_calcula_kpis_y_cumpleanos_semana(self):
        self._authenticate()
        hoy = timezone.localdate()

        persona_b1 = self._crear_persona(
            rut="10.000.000-8",
            nombres="Ben",
            apellidos="DosDias",
            fecha_nacimiento=hoy.replace(year=hoy.year - 12) + timezone.timedelta(days=2),
        )
        ben1 = Beneficiario.objects.create(persona=persona_b1, rama_actual=self.rama, unidad=self.unidad, fecha_ingreso=hoy)

        persona_b2 = self._crear_persona(
            rut="10.000.001-6",
            nombres="Ben",
            apellidos="FueraRango",
            fecha_nacimiento=hoy.replace(year=hoy.year - 13) + timezone.timedelta(days=10),
        )
        ben2 = Beneficiario.objects.create(persona=persona_b2, rama_actual=self.rama, unidad=self.unidad, fecha_ingreso=hoy)

        persona_ap = self._crear_persona(
            rut="10.000.002-4",
            nombres="Apo",
            apellidos="Activo",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.FEMENINO,
        )
        apoderado = Apoderado.objects.create(persona=persona_ap)
        ApoderadoBeneficiario.objects.create(
            apoderado=apoderado,
            beneficiario=ben1,
            parentesco=Parentesco.MADRE,
            autoriza_salidas_terreno=True,
            fecha_autorizacion=hoy,
        )

        persona_a1 = self._crear_persona(
            rut="10.000.003-2",
            nombres="Adulto",
            apellidos="TresDias",
            fecha_nacimiento=hoy.replace(year=hoy.year - 30) + timezone.timedelta(days=3),
        )
        adulto1 = Adulto.objects.create(
            persona=persona_a1,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=hoy + timezone.timedelta(days=30),
        )

        persona_a2 = self._crear_persona(
            rut="10.000.004-0",
            nombres="Adulto",
            apellidos="SinFormacion",
            fecha_nacimiento="1988-05-01",
        )
        adulto2 = Adulto.objects.create(
            persona=persona_a2,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=hoy + timezone.timedelta(days=30),
        )

        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto1, rol=RolAdultoUnidad.ASISTENTE)
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto2, rol=RolAdultoUnidad.COLABORADOR)

        grado = GradoFormacion.objects.create(nivel="Basico", especialidad="Tropa")
        AdultoGradoFormacion.objects.create(adulto=adulto1, grado=grado, fecha_obtencion=hoy)

        response = self.client.get(reverse("v1:dashboard-grupo", kwargs={"pk": self.grupo.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["kpis"]["total_beneficiarios_activos"], 2)
        self.assertEqual(response.data["data"]["kpis"]["total_adultos_activos"], 3)
        self.assertEqual(response.data["data"]["kpis"]["total_miembros"], 5)
        self.assertEqual(response.data["data"]["kpis"]["adultos_con_formacion"], 1)
        self.assertEqual(response.data["data"]["kpis"]["porcentaje_adultos_con_formacion"], 33.33)
        self.assertEqual(response.data["data"]["kpis"]["beneficiarios_con_apoderado_activo"], 1)
        self.assertEqual(response.data["data"]["kpis"]["porcentaje_beneficiarios_con_apoderado_activo"], 50.0)

        cumpleanos = response.data["data"]["alertas"]["cumpleanos_semana"]
        self.assertEqual(len(cumpleanos), 2)
        self.assertEqual(cumpleanos[0]["dias_restantes"], 2)
        self.assertEqual(cumpleanos[0]["tipo"], "BENEFICIARIO")
        self.assertEqual(cumpleanos[1]["dias_restantes"], 3)
        self.assertEqual(cumpleanos[1]["tipo"], "ADULTO")

        tipos = {item["tipo"] for item in cumpleanos}
        self.assertEqual(tipos, {"BENEFICIARIO", "ADULTO"})


class RbacApiTests(APITestCase):
    def setUp(self):
        self.zona = Zona.objects.create(nombre="Zona RBAC")
        self.distrito = Distrito.objects.create(nombre="Distrito RBAC", zona=self.zona)
        self.rama = Rama.objects.create(
            nombre="Rama RBAC",
            edad_minima=11,
            edad_maxima=15,
            composicion_permitida=ComposicionPermitida.MIXTA,
            nomenclatura_subgrupos="Patrullas",
            activa=True,
        )
        self.grupo = GrupoScout.objects.create(
            nombre_oficial="Grupo RBAC",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Dir",
            comuna="Comuna",
        )
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=self.rama, nombre="Unidad RBAC")
        self.unidad_misma_grupo = Unidad.objects.create(
            grupo=self.grupo,
            rama=self.rama,
            nombre="Unidad RBAC Mismo Grupo",
        )
        self.grupo_otro = GrupoScout.objects.create(
            nombre_oficial="Grupo RBAC Otro",
            distrito=self.distrito,
            zona=self.zona,
            tipo_grupo=TipoGrupo.PLURICONFESIONAL,
            direccion="Dir",
            comuna="Comuna",
        )
        self.unidad_otra = Unidad.objects.create(grupo=self.grupo_otro, rama=self.rama, nombre="Unidad RBAC Otra")

        self.staff = get_user_model().objects.create_user("staff", password="testpass123", is_staff=True)

        self.user_resp = get_user_model().objects.create_user("resp", password="testpass123")
        persona_resp = Persona.objects.create(
            usuario=self.user_resp,
            rut="20.000.000-5",
            nombres="Resp",
            apellidos="Grupo",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="1",
        )
        adulto_resp = Adulto.objects.create(
            persona=persona_resp,
            rol_principal=RolAdulto.RESP_GRUPO,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        ConsejoGrupo.objects.create(grupo=self.grupo, responsable_grupo=adulto_resp)

        self.user_asistente = get_user_model().objects.create_user("asis", password="testpass123")
        persona_asis = Persona.objects.create(
            usuario=self.user_asistente,
            rut="20.000.001-3",
            nombres="Asis",
            apellidos="Unidad",
            fecha_nacimiento="1985-01-01",
            sexo=SexoPersona.FEMENINO,
            direccion="Dir",
            telefono="2",
        )
        adulto_asis = Adulto.objects.create(
            persona=persona_asis,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto_asis, rol=RolAdultoUnidad.ASISTENTE)

        self.user_colab = get_user_model().objects.create_user("colab", password="testpass123")
        persona_colab = Persona.objects.create(
            usuario=self.user_colab,
            rut="20.000.002-1",
            nombres="Colab",
            apellidos="Unidad",
            fecha_nacimiento="1986-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="3",
        )
        adulto_colab = Adulto.objects.create(
            persona=persona_colab,
            rol_principal=RolAdulto.COLABORADOR,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto_colab, rol=RolAdultoUnidad.COLABORADOR)

        persona_ben = Persona.objects.create(
            rut="20.000.003-k",
            nombres="Ben",
            apellidos="Uno",
            fecha_nacimiento="2013-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="4",
        )
        self.beneficiario = Beneficiario.objects.create(
            persona=persona_ben,
            rama_actual=self.rama,
            unidad=self.unidad,
            fecha_ingreso=timezone.localdate(),
        )
        persona_ben_otro = Persona.objects.create(
            rut="20.000.009-0",
            nombres="Ben",
            apellidos="Otro",
            fecha_nacimiento="2013-02-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="9",
        )
        self.beneficiario_otro = Beneficiario.objects.create(
            persona=persona_ben_otro,
            rama_actual=self.rama,
            unidad=self.unidad_otra,
            fecha_ingreso=timezone.localdate(),
        )
        persona_ben_mismo_grupo = Persona.objects.create(
            rut="20.000.010-4",
            nombres="Ben",
            apellidos="MismoGrupo",
            fecha_nacimiento="2013-03-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="10",
        )
        self.beneficiario_mismo_grupo = Beneficiario.objects.create(
            persona=persona_ben_mismo_grupo,
            rama_actual=self.rama,
            unidad=self.unidad_misma_grupo,
            fecha_ingreso=timezone.localdate(),
        )

        self.user_apo = get_user_model().objects.create_user("apo", password="testpass123")
        persona_apo = Persona.objects.create(
            usuario=self.user_apo,
            rut="20.000.004-8",
            nombres="Apo",
            apellidos="Uno",
            fecha_nacimiento="1981-01-01",
            sexo=SexoPersona.FEMENINO,
            direccion="Dir",
            telefono="5",
        )
        apoderado = Apoderado.objects.create(persona=persona_apo)
        self.rel = ApoderadoBeneficiario.objects.create(
            apoderado=apoderado,
            beneficiario=self.beneficiario,
            parentesco=Parentesco.MADRE,
            autoriza_salidas_terreno=True,
            fecha_autorizacion=timezone.localdate(),
        )
        self.area = AreaDesarrollo.objects.create(codigo="RBAC", nombre="RBAC", definicion="RBAC")
        self.user_sin_persona = get_user_model().objects.create_user("nopersona", password="testpass123")

    def _auth(self, username):
        login = self.client.post(reverse("v1:auth-token"), {"username": username, "password": "testpass123"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}")

    def test_dashboard_visible_para_adulto_unidad(self):
        self._auth("colab")
        response = self.client.get(reverse("v1:dashboard-grupo", kwargs={"pk": self.grupo.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_colaborador_no_puede_editar_beneficiario(self):
        self._auth("colab")
        response = self.client.patch(
            reverse("v1:beneficiarios-detail", kwargs={"pk": self.beneficiario.id}),
            {"fecha_ingreso": str(timezone.localdate())},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_asistente_puede_editar_beneficiario(self):
        self._auth("asis")
        response = self.client.patch(
            reverse("v1:beneficiarios-detail", kwargs={"pk": self.beneficiario.id}),
            {"fecha_ingreso": str(timezone.localdate())},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_asistente_puede_crear_progresion_unidad(self):
        self._auth("asis")
        response = self.client.post(
            reverse("v1:progresiones-list"),
            {
                "beneficiario": self.beneficiario.id,
                "fecha": str(timezone.localdate()),
                "tipo": TipoRegistroProgresion.DURANTE_CICLO,
                "texto": "Avance",
                "areas": [self.area.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_apoderado_edita_solo_su_persona(self):
        self._auth("apo")
        response_ok = self.client.patch(
            reverse("v1:personas-detail", kwargs={"pk": self.user_apo.persona.id}),
            {"telefono": "999"},
            format="json",
        )
        self.assertEqual(response_ok.status_code, status.HTTP_200_OK)

        response_forbidden = self.client.patch(
            reverse("v1:personas-detail", kwargs={"pk": self.beneficiario.persona.id}),
            {"telefono": "888"},
            format="json",
        )
        self.assertEqual(response_forbidden.status_code, status.HTTP_403_FORBIDDEN)

    def test_responsable_grupo_puede_editar_unidad(self):
        self._auth("resp")
        response = self.client.patch(
            reverse("v1:unidades-detail", kwargs={"pk": self.unidad.id}),
            {"cupo_maximo": 40},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_usuario_autenticado_sin_persona_no_accede_dominio(self):
        self._auth("nopersona")
        grupos = self.client.get(reverse("v1:grupos-list"))
        self.assertEqual(grupos.status_code, status.HTTP_200_OK)
        self.assertEqual(grupos.data["data"], [])

        dashboard = self.client.get(reverse("v1:dashboard-grupo", kwargs={"pk": self.grupo.id}))
        self.assertEqual(dashboard.status_code, status.HTTP_403_FORBIDDEN)

    def test_colaborador_no_lista_beneficiarios_de_otra_unidad(self):
        self._auth("colab")
        response = self.client.get(reverse("v1:beneficiarios-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data["data"]}
        self.assertIn(self.beneficiario.id, ids)
        self.assertNotIn(self.beneficiario_otro.id, ids)

    def test_colaborador_no_lista_subgrupos_de_otra_unidad(self):
        subgrupo_local = Subgrupo.objects.create(nombre="Patrulla Local", unidad=self.unidad)
        subgrupo_otro = Subgrupo.objects.create(nombre="Patrulla Otra", unidad=self.unidad_otra)
        self._auth("colab")
        response = self.client.get(reverse("v1:subgrupos-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data["data"]}
        self.assertIn(subgrupo_local.id, ids)
        self.assertNotIn(subgrupo_otro.id, ids)

    def test_adulto_unidad_ve_solo_sus_unidades_en_estructura_grupo(self):
        subgrupo_local = Subgrupo.objects.create(nombre="Patrulla Local Estructura", unidad=self.unidad)
        Subgrupo.objects.create(nombre="Patrulla Privada", unidad=self.unidad_misma_grupo)
        persona_adulta_privada = Persona.objects.create(
            rut="20.000.011-2",
            nombres="Adulta",
            apellidos="Privada",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.FEMENINO,
            direccion="Dir",
            telefono="11",
        )
        adulta_privada = Adulto.objects.create(
            persona=persona_adulta_privada,
            rol_principal=RolAdulto.DIRIGENTE,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        AdultoUnidadRol.objects.create(
            unidad=self.unidad_misma_grupo,
            adulto=adulta_privada,
            rol=RolAdultoUnidad.ASISTENTE,
        )
        self._auth("colab")

        response = self.client.get(reverse("v1:grupos-estructura", kwargs={"pk": self.grupo.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        estructura = response.data["data"]
        unidades = [unidad for rama in estructura["ramas"] for unidad in rama["unidades"]]
        unit_ids = {unidad["id"] for unidad in unidades}
        serialized = str(estructura)

        self.assertEqual(unit_ids, {self.unidad.id})
        self.assertEqual(estructura["resumen"]["total_unidades"], 1)
        self.assertIn(subgrupo_local.id, {item["id"] for item in unidades[0]["subgrupos"]})
        self.assertNotIn(self.unidad_misma_grupo.id, unit_ids)
        self.assertNotIn(self.beneficiario_mismo_grupo.persona.rut, serialized)
        self.assertNotIn("MismoGrupo", serialized)
        self.assertNotIn(persona_adulta_privada.rut, serialized)
        self.assertNotIn("Privada", serialized)

    def test_responsable_grupo_ve_estructura_completa(self):
        self._auth("resp")

        response = self.client.get(reverse("v1:grupos-estructura", kwargs={"pk": self.grupo.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unit_ids = {unidad["id"] for rama in response.data["data"]["ramas"] for unidad in rama["unidades"]}
        self.assertEqual(unit_ids, {self.unidad.id, self.unidad_misma_grupo.id})

    def test_apoderado_y_usuario_sin_persona_no_acceden_estructura(self):
        for username in ("apo", "nopersona"):
            self._auth(username)
            response = self.client.get(reverse("v1:grupos-estructura", kwargs={"pk": self.grupo.id}))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_apoderado_no_lista_beneficiarios_no_relacionados(self):
        self._auth("apo")
        response = self.client.get(reverse("v1:beneficiarios-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data["data"]}
        self.assertEqual(ids, {self.beneficiario.id})

    def test_listados_omiten_pii_y_ruta_de_certificado(self):
        self._auth("staff")

        personas = self.client.get(reverse("v1:personas-list"))
        adultos = self.client.get(reverse("v1:adultos-list"))

        self.assertEqual(personas.status_code, status.HTTP_200_OK)
        self.assertEqual(set(personas.data["data"][0]), {"id", "nombre_completo", "estado"})
        self.assertNotIn("rut", str(personas.data["data"]))
        self.assertNotIn("telefono", str(personas.data["data"]))
        self.assertNotIn("email", str(personas.data["data"]))
        self.assertEqual(adultos.status_code, status.HTTP_200_OK)
        self.assertNotIn("certificado_inhabilidades", str(adultos.data["data"]))

    def test_apoderado_no_lista_coapoderados(self):
        persona_coapoderado = Persona.objects.create(
            rut="20.000.012-0",
            nombres="Co",
            apellidos="Apoderado",
            fecha_nacimiento="1982-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Dir",
            telefono="12",
        )
        coapoderado = Apoderado.objects.create(persona=persona_coapoderado)
        ApoderadoBeneficiario.objects.create(
            apoderado=coapoderado,
            beneficiario=self.beneficiario,
            parentesco=Parentesco.PADRE,
        )
        self._auth("apo")

        apoderados = self.client.get(reverse("v1:apoderados-list"))

        self.assertEqual(apoderados.status_code, status.HTTP_200_OK)
        self.assertEqual({item["id"] for item in apoderados.data["data"]}, {self.rel.apoderado_id})
        self.assertNotIn("Co Apoderado", str(apoderados.data["data"]))

    def test_usuario_hibrido_suma_alcance_apoderado_y_unidad(self):
        adulto = Adulto.objects.create(
            persona=self.user_apo.persona,
            rol_principal=RolAdulto.APODERADO,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )
        AdultoUnidadRol.objects.create(unidad=self.unidad_otra, adulto=adulto, rol=RolAdultoUnidad.ASISTENTE)
        self._auth("apo")

        response = self.client.get(reverse("v1:beneficiarios-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({item["id"] for item in response.data["data"]}, {self.beneficiario.id, self.beneficiario_otro.id})

    def test_beneficiarios_filtran_sin_ampliar_alcance(self):
        self._auth("colab")

        response = self.client.get(reverse("v1:beneficiarios-list"), {"unidad_id": self.unidad_otra.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])

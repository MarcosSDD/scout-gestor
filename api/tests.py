from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona
from organizacion.models import GrupoScout, TipoGrupo
from personas.models import Adulto, Apoderado, Beneficiario, Parentesco, Persona, RolAdulto, SexoPersona
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Subgrupo, Unidad


class Stage0ApiTests(APITestCase):
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


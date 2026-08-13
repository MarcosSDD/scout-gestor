from io import BytesIO
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from pypdf import PdfWriter
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from personas.models import Adulto, Persona, RolAdulto, SexoPersona


THROTTLE_TEST_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
        "auth": "1/min",
        "auth_refresh": "1/min",
        "file_upload": "1/min",
    },
}


@override_settings(
    REST_FRAMEWORK=THROTTLE_TEST_REST_FRAMEWORK,
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "api-throttling-integration-tests",
        }
    },
)
class ThrottlingIntegrationTests(APITestCase):
    """Exercise the configured scoped throttles through real API requests."""

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.media_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_directory.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        throttle_rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        self.throttle_rates_patcher = patch.object(ScopedRateThrottle, "THROTTLE_RATES", throttle_rates)
        self.throttle_rates_patcher.start()
        self.addCleanup(self.throttle_rates_patcher.stop)
        self.user = get_user_model().objects.create_user(
            username="throttle-user",
            email="throttle@example.test",
            password="testpass123",
            is_staff=True,
        )

    def _assert_throttled_envelope(self, response):
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(set(response.data), {"success", "error"})
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "throttled")
        self.assertIn("detail", response.data["error"]["details"])
        self.assertIn("throttled", response.data["error"]["message"].lower())

    def _login(self):
        response = self.client.post(
            reverse("v1:auth-token"),
            {"email": self.user.email, "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["data"]

    @staticmethod
    def _photo(name):
        image = Image.new("RGB", (1, 1), color="white")
        content = BytesIO()
        image.save(content, format="PNG")
        return SimpleUploadedFile(name, content.getvalue(), content_type="image/png")

    @staticmethod
    def _certificate(name):
        content = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(content)
        return SimpleUploadedFile(name, content.getvalue(), content_type="application/pdf")

    def test_login_returns_normalized_429_after_auth_scope_limit(self):
        self._login()

        response = self.client.post(
            reverse("v1:auth-token"),
            {"email": self.user.email, "password": "testpass123"},
            format="json",
        )

        self._assert_throttled_envelope(response)

    def test_refresh_returns_normalized_429_after_auth_refresh_scope_limit(self):
        refresh = self._login()["refresh"]
        first_refresh = self.client.post(reverse("v1:auth-token-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(first_refresh.status_code, status.HTTP_200_OK)

        response = self.client.post(reverse("v1:auth-token-refresh"), {"refresh": refresh}, format="json")

        self._assert_throttled_envelope(response)

    def test_authenticated_multipart_photo_patch_returns_429_after_file_upload_scope_limit(self):
        persona = Persona.objects.create(
            rut="12.345.678-5",
            nombres="Persona",
            apellidos="Throttle",
            fecha_nacimiento="1990-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Direccion",
            telefono="123456789",
            email="persona.throttle@example.test",
        )
        tokens = self._login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        url = reverse("v1:personas-detail", kwargs={"pk": persona.pk})

        first_patch = self.client.patch(url, {"foto": self._photo("first.png")}, format="multipart")
        self.assertEqual(first_patch.status_code, status.HTTP_200_OK, first_patch.data)
        self.assertTrue(first_patch.data["success"])

        response = self.client.patch(url, {"foto": self._photo("second.png")}, format="multipart")

        self._assert_throttled_envelope(response)

    def test_authenticated_multipart_certificate_renewal_returns_429_after_file_upload_scope_limit(self):
        persona = Persona.objects.create(
            rut="12.345.678-5",
            nombres="Adulto",
            apellidos="Throttle",
            fecha_nacimiento="1980-01-01",
            sexo=SexoPersona.MASCULINO,
            direccion="Direccion",
            telefono="123456789",
            email="adulto.throttle@example.test",
        )
        adulto = Adulto.objects.create(
            persona=persona,
            rol_principal=RolAdulto.GUIA,
            certificado_inhabilidades=self._certificate("original.pdf"),
            certificado_vigencia_hasta="2030-01-01",
        )
        tokens = self._login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        url = reverse("v1:adultos-certificado", kwargs={"pk": adulto.pk})

        first_patch = self.client.patch(
            url,
            {
                "certificado_inhabilidades": self._certificate("renewed.pdf"),
                "certificado_vigencia_hasta": "2030-01-02",
            },
            format="multipart",
        )
        self.assertEqual(first_patch.status_code, status.HTTP_200_OK, first_patch.data)
        self.assertTrue(first_patch.data["success"])

        response = self.client.patch(
            url,
            {
                "certificado_inhabilidades": self._certificate("renewed-again.pdf"),
                "certificado_vigencia_hasta": "2030-01-03",
            },
            format="multipart",
        )

        self._assert_throttled_envelope(response)

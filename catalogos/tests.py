from django.test import TestCase
from django.core.exceptions import ValidationError

from catalogos.models import ComposicionPermitida, Rama


class RamaModelTests(TestCase):
    def test_rango_etario_valido(self):
        rama = Rama(
            nombre="Clan",
            edad_minima=18,
            edad_maxima=21,
            composicion_permitida=ComposicionPermitida.MIXTA,
            nomenclatura_subgrupos="Equipos",
        )
        rama.full_clean()

    def test_rango_etario_invalido(self):
        rama = Rama(
            nombre="Error",
            edad_minima=12,
            edad_maxima=12,
            composicion_permitida=ComposicionPermitida.MIXTA,
            nomenclatura_subgrupos="Patrullas",
        )
        with self.assertRaises(ValidationError):
            rama.full_clean()

# Create your tests here.

from django.core.management.base import BaseCommand

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona


RAMAS_BASE = [
    {
        "nombre": "Golondrinas",
        "edad_minima": 7,
        "edad_maxima": 11,
        "composicion_permitida": ComposicionPermitida.MIXTA,
        "nomenclatura_subgrupos": "Nidos",
    },
    {
        "nombre": "Lobatos",
        "edad_minima": 7,
        "edad_maxima": 11,
        "composicion_permitida": ComposicionPermitida.MIXTA,
        "nomenclatura_subgrupos": "Seisenas",
    },
    {
        "nombre": "Guías",
        "edad_minima": 11,
        "edad_maxima": 15,
        "composicion_permitida": ComposicionPermitida.SOLO_MUJERES,
        "nomenclatura_subgrupos": "Patrullas",
    },
    {
        "nombre": "Scouts",
        "edad_minima": 11,
        "edad_maxima": 15,
        "composicion_permitida": ComposicionPermitida.SOLO_HOMBRES,
        "nomenclatura_subgrupos": "Patrullas",
    },
    {
        "nombre": "Pioneras y Pioneros",
        "edad_minima": 15,
        "edad_maxima": 18,
        "composicion_permitida": ComposicionPermitida.MIXTA,
        "nomenclatura_subgrupos": "Unidades",
    },
    {
        "nombre": "Caminantes",
        "edad_minima": 18,
        "edad_maxima": 21,
        "composicion_permitida": ComposicionPermitida.MIXTA,
        "nomenclatura_subgrupos": "Equipos",
    },
]


class Command(BaseCommand):
    help = "Carga catalogos base (ramas, zona y distritos de ejemplo)"

    def handle(self, *args, **options):
        zona_rios, _ = Zona.objects.get_or_create(nombre="Zona De Los Ríos")
        Distrito.objects.get_or_create(nombre="Distrito Valdivia", zona=zona_rios)
        Distrito.objects.get_or_create(nombre="Distrito Ejemplo", zona=zona_rios)

        creadas = 0
        for rama_data in RAMAS_BASE:
            _, created = Rama.objects.update_or_create(
                nombre=rama_data["nombre"],
                defaults=rama_data,
            )
            if created:
                creadas += 1

        self.stdout.write(self.style.SUCCESS(f"Carga completada. Ramas creadas: {creadas}"))

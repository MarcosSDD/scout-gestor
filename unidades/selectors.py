from django.db.models import Count

from unidades.models import AdultoUnidadRol


def duplicate_adult_unit_role_pairs():
    """Return duplicate adult/unit assignments that block the role migration."""
    return (
        AdultoUnidadRol.objects.values("unidad_id", "adulto_id")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .order_by("unidad_id", "adulto_id")
    )

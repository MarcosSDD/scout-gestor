from django.db import migrations, models
from django.db.models import Count


def validate_one_role_per_adult_unit(apps, schema_editor):
    Assignment = apps.get_model("unidades", "AdultoUnidadRol")
    duplicates = list(
        Assignment.objects.values("unidad_id", "adulto_id")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .order_by("unidad_id", "adulto_id")[:20]
    )
    if duplicates:
        pairs = ", ".join(f"unidad={row['unidad_id']}, adulto={row['adulto_id']}" for row in duplicates)
        raise RuntimeError(
            "No se puede aplicar la regla de un rol por adulto y unidad. "
            f"Corrija las asignaciones duplicadas antes de migrar: {pairs}. "
            "Ejecute verificar_roles_adulto_unidad para obtener el reporte completo."
        )


class Migration(migrations.Migration):
    dependencies = [("unidades", "0002_historicaladultounidadrol_historicalsubgrupo_and_more")]

    operations = [
        migrations.RunPython(validate_one_role_per_adult_unit, validate_one_role_per_adult_unit),
        migrations.RemoveConstraint(model_name="adultounidadrol", name="uq_adulto_rol_unidad"),
        migrations.AddConstraint(
            model_name="adultounidadrol",
            constraint=models.UniqueConstraint(fields=("unidad", "adulto"), name="uq_adulto_por_unidad"),
        ),
    ]

from django.core.management.base import BaseCommand, CommandError

from unidades.selectors import duplicate_adult_unit_role_pairs


class Command(BaseCommand):
    help = "Reporta asignaciones duplicadas de adulto por unidad antes de aplicar la migracion."

    def handle(self, *args, **options):
        duplicates = list(duplicate_adult_unit_role_pairs())
        if not duplicates:
            self.stdout.write(self.style.SUCCESS("No existen asignaciones duplicadas de adulto por unidad."))
            return
        for row in duplicates:
            self.stdout.write(f"unidad={row['unidad_id']} adulto={row['adulto_id']} roles={row['total']}")
        raise CommandError("Corrija las asignaciones duplicadas antes de aplicar la migracion.")

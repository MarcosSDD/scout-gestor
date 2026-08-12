from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from organizacion.services import ensure_demo_seed_is_allowed, seed_demo_grupo


class Command(BaseCommand):
    help = "Crea un grupo demo local con datos y usuarios RBAC de prueba."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Elimina primero los datos demo identificados.")
        parser.add_argument("--no-input", action="store_true", help="Confirma el uso no interactivo de --reset.")

    def handle(self, *args, **options):
        try:
            ensure_demo_seed_is_allowed()
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        if options["reset"] and not options["no_input"]:
            raise CommandError("--reset requiere --no-input para evitar eliminaciones accidentales.")
        try:
            grupo = seed_demo_grupo(reset=options["reset"])
        except ValidationError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Grupo demo listo: {grupo.nombre_oficial} (id={grupo.pk})."))

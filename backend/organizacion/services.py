"""Servicios de escritura para la organización scout."""

from datetime import date
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone
from pypdf import PdfWriter

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona
from organizacion.models import ConsejoGrupo, GrupoScout, TipoGrupo
from personas.models import (
    Adulto,
    Apoderado,
    ApoderadoBeneficiario,
    Beneficiario,
    Parentesco,
    RolAdulto,
    SexoPersona,
    Persona,
)
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Subgrupo, SubgrupoMiembro, Unidad


DEMO_GROUP_NAME = "Grupo Scout Demo"
DEMO_PASSWORD = "ScoutDemo!2026"
DEMO_EMAIL_DOMAIN = "demo.scout.local"
DEMO_MARKER = "SCOUT_DEMO_SEED_V1"
DEMO_GROUP_REFERENCE = DEMO_MARKER
DEMO_USERNAMES = (
    "demo_staff",
    "demo_responsable_grupo",
    "demo_responsable_golondrinas",
    "demo_responsable_lobatos",
    "demo_responsable_guias",
    "demo_responsable_scouts",
    "demo_responsable_pioneros",
    "demo_responsable_caminantes",
    "demo_apoderado",
    "demo_sin_persona",
)
DEMO_USER_EMAILS = {
    "demo_responsable_grupo": f"20000201@{DEMO_EMAIL_DOMAIN}",
    "demo_responsable_golondrinas": f"20000202@{DEMO_EMAIL_DOMAIN}",
    "demo_responsable_lobatos": f"20000203@{DEMO_EMAIL_DOMAIN}",
    "demo_responsable_guias": f"20000204@{DEMO_EMAIL_DOMAIN}",
    "demo_responsable_scouts": f"20000205@{DEMO_EMAIL_DOMAIN}",
    "demo_responsable_pioneros": f"20000206@{DEMO_EMAIL_DOMAIN}",
    "demo_responsable_caminantes": f"20000207@{DEMO_EMAIL_DOMAIN}",
    "demo_apoderado": f"20000101@{DEMO_EMAIL_DOMAIN}",
}
_LEGACY_DEMO_USERNAMES = ("demo_apoderado_1", "demo_apoderado_2", "demo_apoderado_3")
DEMO_PERSON_NUMBERS = (
    tuple(range(20_000_001, 20_000_019))
    + tuple(range(20_000_101, 20_000_119))
    + tuple(range(20_000_201, 20_000_208))
)

RAMA_DEMO = (
    ("Golondrinas", "Unidad Golondrinas Demo", "Nido Demo", SexoPersona.FEMENINO),
    ("Lobatos", "Unidad Lobatos Demo", "Seisena Demo", SexoPersona.MASCULINO),
    ("Guías", "Unidad Guías Demo", "Patrulla Demo", SexoPersona.FEMENINO),
    ("Scouts", "Unidad Scouts Demo", "Patrulla Demo", SexoPersona.MASCULINO),
    ("Pioneras y Pioneros", "Unidad Pioneros Demo", "Equipo Demo", SexoPersona.FEMENINO),
    ("Caminantes", "Unidad Caminantes Demo", "Equipo Demo", SexoPersona.MASCULINO),
)


def ensure_demo_seed_is_allowed() -> None:
    """Impide crear credenciales conocidas fuera de SQLite de desarrollo."""
    if connection.vendor != "sqlite" or not settings.DEBUG:
        raise ValidationError("seed_grupo_demo solo puede ejecutarse con SQLite y DEBUG=True.")


def _save(instance, user):
    instance.full_clean()
    if hasattr(instance, "history"):
        instance._history_user = user
    instance.save()
    return instance


def _get_or_create_validated(model, *, lookup: dict, defaults: dict, user):
    instance = model.objects.filter(**lookup).first()
    if instance is not None:
        return instance, False
    instance = model(**lookup, **defaults)
    return _save(instance, user), True


def _rut(number: int) -> str:
    factors = (2, 3, 4, 5, 6, 7)
    total = sum(int(digit) * factors[index % len(factors)] for index, digit in enumerate(reversed(str(number))))
    remainder = 11 - (total % 11)
    verifier = "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)
    return f"{number}-{verifier}"


def _birthdate_for_age(age: int) -> date:
    # El 1 de enero garantiza que la edad ya se cumplió en cualquier ejecución anual.
    return date(timezone.localdate().year - age, 1, 1)


def _demo_pdf() -> ContentFile:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(output)
    return ContentFile(output.getvalue(), name="certificado-demo.pdf")


def _user(username: str, *, is_staff: bool = False):
    user_model = get_user_model()
    email = DEMO_USER_EMAILS.get(username, f"{username}@{DEMO_EMAIL_DOMAIN}")
    user = user_model.objects.filter(username=username).first()
    if user is None:
        user = user_model(
            username=username,
            email=email,
            last_name=DEMO_MARKER,
            is_staff=is_staff,
        )
        user.set_password(DEMO_PASSWORD)
        user.full_clean()
        user.save()
    elif user.last_name != DEMO_MARKER:
        raise ValidationError(f"El usuario reservado {username} no tiene los marcadores demo esperados.")
    elif not user.check_password(DEMO_PASSWORD) or user.is_staff != is_staff or user.email != email:
        user.email = email
        user.is_staff = is_staff
        user.set_password(DEMO_PASSWORD)
        user.full_clean()
        user.save()
    return user


def _has_unmarked_reserved_users() -> bool:
    return any(
        user.last_name != DEMO_MARKER
        for user in get_user_model().objects.filter(username__in=DEMO_USERNAMES + _LEGACY_DEMO_USERNAMES)
    )


def _persona(*, number: int, nombres: str, apellidos: str, sexo: str, edad: int, user=None):
    persona, created = _get_or_create_validated(
        Persona,
        lookup={"rut": _rut(number)},
        defaults={
            "usuario": user,
            "nombres": nombres,
            "apellidos": apellidos,
            "fecha_nacimiento": _birthdate_for_age(edad),
            "sexo": sexo,
            "direccion": "Avenida Demo 123, Valdivia",
            "telefono": "+56911111111",
            "email": f"{number}@{DEMO_EMAIL_DOMAIN}",
        }, user=user,
    )
    if not created and user and persona.usuario_id != user.id:
        raise ValidationError(f"La persona demo {_rut(number)} está vinculada a otro usuario.")
    return persona


def _adulto(*, persona: Persona, role: str, user):
    adulto, created = _get_or_create_validated(
        Adulto,
        lookup={"persona": persona},
        defaults={
            "rol_principal": role,
            "certificado_inhabilidades": _demo_pdf(),
            "certificado_vigencia_hasta": timezone.localdate().replace(year=timezone.localdate().year + 1),
        }, user=user,
    )
    return adulto


def _validate_age_and_composition(*, persona: Persona, rama: Rama, unit: Unidad) -> None:
    age = timezone.localdate().year - persona.fecha_nacimiento.year
    if (timezone.localdate().month, timezone.localdate().day) < (persona.fecha_nacimiento.month, persona.fecha_nacimiento.day):
        age -= 1
    if not rama.edad_minima <= age <= rama.edad_maxima:
        raise ValidationError({"persona": f"La edad de {persona} no corresponde a la rama {rama.nombre}."})
    _validate_composition(persona=persona, unit=unit)


def _validate_composition(*, persona: Persona, unit: Unidad) -> None:
    composition = unit.composicion_actual()
    if composition == ComposicionPermitida.SOLO_HOMBRES and persona.sexo != SexoPersona.MASCULINO:
        raise ValidationError({"persona": "La composición de la unidad requiere sexo masculino."})
    if composition == ComposicionPermitida.SOLO_MUJERES and persona.sexo != SexoPersona.FEMENINO:
        raise ValidationError({"persona": "La composición de la unidad requiere sexo femenino."})


def _ensure_demo_reset_is_isolated(demo_ruts: list[str]) -> None:
    """Evita que el reset destruya identidades demo usadas fuera de su dataset."""
    demo_personas = Persona.objects.filter(rut__in=demo_ruts)
    demo_beneficiarios = Beneficiario.objects.filter(persona__in=demo_personas)
    demo_apoderados = Apoderado.objects.filter(persona__in=demo_personas)
    demo_adultos = Adulto.objects.filter(persona__in=demo_personas)
    violations = []

    if _has_unmarked_reserved_users():
        violations.append("Existe un usuario reservado sin los marcadores demo esperados.")
    if Persona.objects.filter(usuario__username__in=DEMO_USERNAMES + _LEGACY_DEMO_USERNAMES).exclude(rut__in=demo_ruts).exists():
        violations.append("Existe una Persona no-demo ligada a un usuario demo.")
    if ApoderadoBeneficiario.objects.filter(
        Q(apoderado__in=demo_apoderados) & ~Q(beneficiario__in=demo_beneficiarios)
        | Q(beneficiario__in=demo_beneficiarios) & ~Q(apoderado__in=demo_apoderados)
    ).exists():
        violations.append("Existen relaciones ApoderadoBeneficiario mixtas con datos no-demo.")
    if SubgrupoMiembro.objects.filter(beneficiario__in=demo_beneficiarios).exclude(
        subgrupo__unidad__grupo__nombre_oficial=DEMO_GROUP_NAME
    ).exists():
        violations.append("Existen membresías demo en subgrupos de unidades o grupos no-demo.")
    if Beneficiario.objects.filter(persona__in=demo_personas).filter(
        Q(unidad__isnull=False) & ~Q(unidad__grupo__nombre_oficial=DEMO_GROUP_NAME)
    ).exists():
        violations.append("Existen beneficiarios demo asignados a unidades no-demo.")
    if AdultoUnidadRol.objects.filter(adulto__in=demo_adultos).exclude(
        unidad__grupo__nombre_oficial=DEMO_GROUP_NAME
    ).exists():
        violations.append("Existen roles de adulto demo en unidades no-demo.")
    if ConsejoGrupo.objects.filter(responsable_grupo__in=demo_adultos).exclude(
        grupo__nombre_oficial=DEMO_GROUP_NAME
    ).exists():
        violations.append("Existen consejos de grupo no-demo con responsables demo.")

    grupo = GrupoScout.objects.filter(nombre_oficial=DEMO_GROUP_NAME).first()
    if grupo:
        if grupo.referencia != DEMO_GROUP_REFERENCE:
            violations.append("El grupo homónimo no tiene el marcador demo esperado.")
        else:
            expected_units = {unit_name: rama_name for rama_name, unit_name, _, _ in RAMA_DEMO}
            units = Unidad.objects.filter(grupo=grupo)
            if units.count() != len(expected_units) or any(
                unit.nombre not in expected_units or unit.rama.nombre != expected_units[unit.nombre] for unit in units.select_related("rama")
            ):
                violations.append("El grupo demo contiene unidades no esperadas.")
            expected_subgroups = {(unit_name, subgroup_name) for _, unit_name, subgroup_name, _ in RAMA_DEMO}
            subgroups = Subgrupo.objects.filter(unidad__grupo=grupo).select_related("unidad")
            if subgroups.count() != len(expected_subgroups) or any(
                (subgroup.unidad.nombre, subgroup.nombre) not in expected_subgroups for subgroup in subgroups
            ):
                violations.append("El grupo demo contiene subgrupos no esperados.")
            expected_beneficiary_ruts = {_rut(number) for number in range(20_000_001, 20_000_019)}
            group_beneficiaries = Beneficiario.objects.filter(unidad__grupo=grupo)
            if group_beneficiaries.count() != 18 or group_beneficiaries.exclude(persona__rut__in=expected_beneficiary_ruts).exists():
                violations.append("El grupo demo contiene beneficiarios no esperados.")
            memberships = SubgrupoMiembro.objects.filter(subgrupo__unidad__grupo=grupo)
            if memberships.count() != 18 or memberships.exclude(beneficiario__persona__rut__in=expected_beneficiary_ruts).exists():
                violations.append("El grupo demo contiene membresías no esperadas.")
            expected_adult_ruts = {_rut(number) for number in range(20_000_202, 20_000_208)}
            adult_roles = AdultoUnidadRol.objects.filter(unidad__grupo=grupo)
            if (
                adult_roles.count() != 6
                or adult_roles.exclude(adulto__persona__rut__in=expected_adult_ruts, rol=RolAdultoUnidad.RESPONSABLE).exists()
            ):
                violations.append("El grupo demo contiene roles adultos no esperados.")
            if not ConsejoGrupo.objects.filter(
                grupo=grupo, responsable_grupo__persona__rut=_rut(20_000_201)
            ).exists():
                violations.append("El consejo del grupo demo no es el esperado.")
            if grupo.comite_cargos.exists():
                violations.append("El grupo demo contiene cargos de comité no esperados.")
            if grupo.instituciones_patrocinantes.exists():
                violations.append("El grupo demo contiene instituciones patrocinantes no esperadas.")

    if violations:
        raise ValidationError({"reset": violations})


def reset_demo_grupo() -> None:
    """Elimina solamente filas y ficheros identificados por las claves fijas del demo."""
    demo_ruts = [_rut(number) for number in DEMO_PERSON_NUMBERS]
    with transaction.atomic():
        _ensure_demo_reset_is_isolated(demo_ruts)
        certificate_names = list(
            Adulto.objects.filter(persona__rut__in=demo_ruts).exclude(certificado_inhabilidades="").values_list(
                "certificado_inhabilidades", flat=True
            )
        )
        GrupoScout.objects.filter(nombre_oficial=DEMO_GROUP_NAME).delete()
        Persona.objects.filter(rut__in=demo_ruts).delete()
        get_user_model().objects.filter(username__in=DEMO_USERNAMES + _LEGACY_DEMO_USERNAMES).delete()
        transaction.on_commit(lambda: [default_storage.delete(name) for name in certificate_names])


@transaction.atomic
def seed_demo_grupo(*, reset: bool = False) -> GrupoScout:
    """Crea el conjunto demo idempotente usado para probar los alcances RBAC."""
    ensure_demo_seed_is_allowed()
    if _has_unmarked_reserved_users():
        raise ValidationError("Existe un usuario reservado sin los marcadores demo esperados.")
    if reset:
        reset_demo_grupo()

    call_command("seed_catalogos")
    zona = Zona.objects.get(nombre="Zona De Los Ríos")
    distrito = Distrito.objects.get(nombre="Distrito Valdivia", zona=zona)
    existing_group = GrupoScout.objects.filter(nombre_oficial=DEMO_GROUP_NAME).first()
    if existing_group and existing_group.referencia != DEMO_GROUP_REFERENCE:
        raise ValidationError("El grupo homónimo no tiene el marcador demo esperado.")
    users = {username: _user(username, is_staff=username == "demo_staff") for username in DEMO_USERNAMES}
    audit_user = users["demo_responsable_grupo"]
    grupo, created = _get_or_create_validated(
        GrupoScout,
        lookup={"nombre_oficial": DEMO_GROUP_NAME},
        defaults={
            "zona": zona,
            "distrito": distrito,
            "tipo_grupo": TipoGrupo.PLURICONFESIONAL,
            "direccion": "Avenida Demo 123",
            "comuna": "Valdivia",
            "referencia": DEMO_GROUP_REFERENCE,
        }, user=audit_user,
    )
    units = {}
    subgroups = {}
    for rama_name, unit_name, subgroup_name, expected_sex in RAMA_DEMO:
        rama = Rama.objects.get(nombre=rama_name)
        unit, unit_created = _get_or_create_validated(
            Unidad, lookup={"grupo": grupo, "nombre": unit_name}, defaults={"rama": rama}, user=audit_user
        )
        if not unit_created and unit.rama_id != rama.id:
            raise ValidationError(f"La unidad demo {unit_name} tiene una rama inconsistente.")
        subgroup, subgroup_created = _get_or_create_validated(
            Subgrupo, lookup={"unidad": unit, "nombre": subgroup_name}, defaults={}, user=audit_user
        )
        if unit.composicion_actual() == ComposicionPermitida.SOLO_HOMBRES and expected_sex != SexoPersona.MASCULINO:
            raise ValidationError(f"La definición demo de {rama_name} no respeta su composición.")
        if unit.composicion_actual() == ComposicionPermitida.SOLO_MUJERES and expected_sex != SexoPersona.FEMENINO:
            raise ValidationError(f"La definición demo de {rama_name} no respeta su composición.")
        units[rama_name], subgroups[rama_name] = unit, subgroup

    ages_by_rama = {
        "Golondrinas": (8, 9, 10),
        "Lobatos": (8, 9, 10),
        "Guías": (12, 13, 14),
        "Scouts": (12, 13, 14),
        "Pioneras y Pioneros": (16, 17, 18),
        "Caminantes": (19, 20, 21),
    }
    leaders = {}
    beneficiary_number = 20_000_001
    for rama_name, _, _, expected_sex in RAMA_DEMO:
        unit = units[rama_name]
        rama = unit.rama
        for member_index, age in enumerate(ages_by_rama[rama_name], start=1):
            sexo = expected_sex if unit.composicion_actual() != ComposicionPermitida.MIXTA else (
                SexoPersona.FEMENINO if member_index != 2 else SexoPersona.MASCULINO
            )
            persona = _persona(
                number=beneficiary_number,
                nombres=f"Beneficiario {member_index}",
                apellidos=f"Demo {rama_name}",
                sexo=sexo,
                edad=age,
            )
            _validate_age_and_composition(persona=persona, rama=rama, unit=unit)
            beneficiary, _ = _get_or_create_validated(
                Beneficiario,
                lookup={"persona": persona},
                defaults={"rama_actual": rama, "unidad": unit, "fecha_ingreso": timezone.localdate()},
                user=audit_user,
            )
            _, membership_created = _get_or_create_validated(
                SubgrupoMiembro,
                lookup={"subgrupo": subgroups[rama_name], "beneficiario": beneficiary},
                defaults={},
                user=audit_user,
            )
            if not membership_created and beneficiary.unidad_id != unit.id:
                raise ValidationError(f"El beneficiario demo {beneficiary} está en una unidad inconsistente.")
            guardian_persona = _persona(
                number=beneficiary_number + 100,
                nombres=f"Apoderado {member_index}",
                apellidos=f"Demo {rama_name}",
                sexo=sexo,
                edad=40,
                user=users["demo_apoderado"] if beneficiary_number == 20_000_001 else None,
            )
            guardian, _ = _get_or_create_validated(
                Apoderado, lookup={"persona": guardian_persona}, defaults={}, user=audit_user
            )
            _, relationship_created = _get_or_create_validated(
                ApoderadoBeneficiario,
                lookup={"apoderado": guardian, "beneficiario": beneficiary},
                defaults={
                    "parentesco": Parentesco.MADRE if sexo == SexoPersona.FEMENINO else Parentesco.PADRE,
                    "autoriza_salidas_terreno": True,
                    "fecha_autorizacion": timezone.localdate(),
                },
                user=audit_user,
            )
            if not relationship_created and guardian.relaciones_beneficiarios.count() != 1:
                raise ValidationError(f"El apoderado demo {guardian} debe tener exactamente un beneficiario.")
            if member_index == 1:
                leaders[rama_name] = beneficiary
            beneficiary_number += 1

    for rama_name, leader in leaders.items():
        subgroup = subgroups[rama_name]
        if subgroup.lider_juvenil_id is None:
            subgroup.lider_juvenil = leader
            _save(subgroup, audit_user)
        elif subgroup.lider_juvenil_id != leader.id:
            raise ValidationError(f"El subgrupo demo de {rama_name} tiene un líder juvenil inconsistente.")

    group_persona = _persona(
        number=20_000_201, nombres="Rocío", apellidos="Responsable", sexo=SexoPersona.FEMENINO, edad=35,
        user=users["demo_responsable_grupo"],
    )
    group_adult = _adulto(persona=group_persona, role=RolAdulto.RESP_GRUPO, user=audit_user)
    consejo, consejo_created = _get_or_create_validated(
        ConsejoGrupo, lookup={"grupo": grupo}, defaults={"responsable_grupo": group_adult}, user=audit_user
    )
    if not consejo_created and consejo.responsable_grupo_id != group_adult.id:
        raise ValidationError("El consejo demo tiene una persona responsable inconsistente.")

    for index, (rama_name, _, _, expected_sex) in enumerate(RAMA_DEMO, start=202):
        username = f"demo_responsable_{('golondrinas', 'lobatos', 'guias', 'scouts', 'pioneros', 'caminantes')[index - 202]}"
        persona = _persona(
            number=20_000_000 + index, nombres="Responsable", apellidos=rama_name, sexo=expected_sex, edad=30,
            user=users[username],
        )
        adulto = _adulto(persona=persona, role=RolAdulto.DIRIGENTE, user=audit_user)
        _validate_composition(persona=persona, unit=units[rama_name])
        assignment, assignment_created = _get_or_create_validated(
            AdultoUnidadRol, lookup={"unidad": units[rama_name], "adulto": adulto},
            defaults={"rol": RolAdultoUnidad.RESPONSABLE}, user=audit_user,
        )
        if not assignment_created and assignment.rol != RolAdultoUnidad.RESPONSABLE:
            raise ValidationError(f"La unidad demo {rama_name} no tiene su responsable esperado.")

    grupo.recalcular_minimo_miembros(save=False)
    _save(grupo, audit_user)
    return grupo

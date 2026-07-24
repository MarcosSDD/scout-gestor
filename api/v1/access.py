from django.db.models import Q

from organizacion.models import GrupoScout
from personas.models import Adulto, Apoderado, Beneficiario, Persona, RegistroProgresionScout
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Subgrupo, SubgrupoMiembro, Unidad


def is_full_access(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def get_user_persona(user):
    if not user or not user.is_authenticated:
        return None
    return getattr(user, "persona", None)


def get_responsable_grupo_ids(user):
    persona = get_user_persona(user)
    if not persona or not hasattr(persona, "adulto"):
        return []
    return list(persona.adulto.consejos_de_grupo.values_list("grupo_id", flat=True))


def get_unidad_roles(user):
    persona = get_user_persona(user)
    if not persona or not hasattr(persona, "adulto"):
        return AdultoUnidadRol.objects.none()
    return AdultoUnidadRol.objects.filter(adulto=persona.adulto)


def get_unidad_ids(user):
    return list(get_unidad_roles(user).values_list("unidad_id", flat=True))


def get_editable_unidad_ids(user):
    return list(
        get_unidad_roles(user)
        .filter(rol__in=[RolAdultoUnidad.RESPONSABLE, RolAdultoUnidad.ASISTENTE])
        .values_list("unidad_id", flat=True)
    )


def get_accessible_grupos_qs(user):
    if is_full_access(user):
        return GrupoScout.objects.all()

    grupo_ids = set(get_responsable_grupo_ids(user))
    unidad_ids = get_unidad_ids(user)
    if unidad_ids:
        grupo_ids.update(Unidad.objects.filter(id__in=unidad_ids).values_list("grupo_id", flat=True))

    if not grupo_ids:
        return GrupoScout.objects.none()
    return GrupoScout.objects.filter(id__in=grupo_ids)


def get_accessible_unidades_qs(user):
    if is_full_access(user):
        return Unidad.objects.all()

    grupo_ids = get_responsable_grupo_ids(user)
    unidad_ids = set(get_unidad_ids(user))
    if grupo_ids:
        unidad_ids.update(Unidad.objects.filter(grupo_id__in=grupo_ids).values_list("id", flat=True))

    if not unidad_ids:
        return Unidad.objects.none()
    return Unidad.objects.filter(id__in=unidad_ids)


def get_structure_unidades_qs(user, group_id: int):
    """Return only the units whose member data the user may see in a group tree."""
    if is_full_access(user) or can_manage_group_data(user, group_id):
        return Unidad.objects.filter(grupo_id=group_id)

    unidad_ids = get_unidad_ids(user)
    if not unidad_ids:
        return Unidad.objects.none()
    return Unidad.objects.filter(grupo_id=group_id, id__in=unidad_ids)


def get_accessible_beneficiarios_qs(user):
    if is_full_access(user):
        return Beneficiario.objects.all()

    persona = get_user_persona(user)
    if not persona:
        return Beneficiario.objects.none()

    filters = Q(pk__in=[])
    if persona and hasattr(persona, "apoderado"):
        filters |= Q(relaciones_apoderados__apoderado=persona.apoderado)

    unidad_ids = list(get_accessible_unidades_qs(user).values_list("id", flat=True))
    if unidad_ids:
        filters |= Q(unidad_id__in=unidad_ids)
    return Beneficiario.objects.filter(filters).distinct()


def get_accessible_adultos_qs(user):
    if is_full_access(user):
        return Adulto.objects.all()

    persona = get_user_persona(user)
    if persona and hasattr(persona, "adulto"):
        own = Q(persona=persona)
    else:
        own = Q(pk__in=[])

    unidad_ids = list(get_accessible_unidades_qs(user).values_list("id", flat=True))
    by_unit = Q(asignaciones_unidad__unidad_id__in=unidad_ids) if unidad_ids else Q(pk__in=[])
    return Adulto.objects.filter(own | by_unit).distinct()


def get_accessible_apoderados_qs(user):
    if is_full_access(user):
        return Apoderado.objects.all()

    persona = get_user_persona(user)
    if not persona:
        return Apoderado.objects.none()

    filters = Q(pk__in=[])
    if persona and hasattr(persona, "apoderado"):
        filters |= Q(persona=persona)

    if hasattr(persona, "adulto"):
        beneficiario_ids = list(get_accessible_beneficiarios_qs(user).values_list("id", flat=True))
        if beneficiario_ids:
            filters |= Q(relaciones_beneficiarios__beneficiario_id__in=beneficiario_ids)
    return Apoderado.objects.filter(filters).distinct()


def get_accessible_personas_qs(user):
    if is_full_access(user):
        return Persona.objects.all()

    persona = get_user_persona(user)
    if not persona:
        return Persona.objects.none()

    filters = Q(id=persona.id)
    filters |= Q(beneficiario__in=get_accessible_beneficiarios_qs(user))
    filters |= Q(adulto__in=get_accessible_adultos_qs(user))
    filters |= Q(apoderado__in=get_accessible_apoderados_qs(user))
    return Persona.objects.filter(filters).distinct()


def get_accessible_progresiones_qs(user):
    if is_full_access(user):
        return RegistroProgresionScout.objects.all()
    return RegistroProgresionScout.objects.filter(beneficiario__in=get_accessible_beneficiarios_qs(user)).distinct()


def can_manage_group_data(user, group_id: int) -> bool:
    if is_full_access(user):
        return True
    return group_id in set(get_responsable_grupo_ids(user))


def can_edit_beneficiario(user, beneficiario: Beneficiario) -> bool:
    if is_full_access(user):
        return True
    unidad_id = beneficiario.unidad_id
    if not unidad_id:
        return False
    if can_manage_group_data(user, beneficiario.unidad.grupo_id):
        return True
    return unidad_id in set(get_editable_unidad_ids(user))


def can_edit_progresion(user, progresion: RegistroProgresionScout) -> bool:
    return can_edit_beneficiario(user, progresion.beneficiario)


def can_edit_persona(user, persona: Persona) -> bool:
    if is_full_access(user):
        return True
    user_persona = get_user_persona(user)
    if user_persona and user_persona.id == persona.id and hasattr(user_persona, "apoderado"):
        return True

    grupo_id = None
    if hasattr(persona, "beneficiario") and persona.beneficiario.unidad_id:
        grupo_id = persona.beneficiario.unidad.grupo_id
    elif hasattr(persona, "adulto"):
        grupo_id = persona.adulto.asignaciones_unidad.values_list("unidad__grupo_id", flat=True).first()
    elif hasattr(persona, "apoderado"):
        grupo_id = (
            persona.apoderado.relaciones_beneficiarios.values_list("beneficiario__unidad__grupo_id", flat=True).first()
        )
    return bool(grupo_id and can_manage_group_data(user, grupo_id))


def can_view_dashboard_group(user, group_id: int) -> bool:
    return get_accessible_grupos_qs(user).filter(id=group_id).exists()


def get_accessible_subgrupos_qs(user):
    if is_full_access(user):
        return Subgrupo.objects.all()
    return Subgrupo.objects.filter(unidad__in=get_accessible_unidades_qs(user))


def get_accessible_subgrupo_miembros_qs(user):
    if is_full_access(user):
        return SubgrupoMiembro.objects.all()
    return SubgrupoMiembro.objects.filter(subgrupo__in=get_accessible_subgrupos_qs(user))

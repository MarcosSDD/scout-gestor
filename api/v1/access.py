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
    return RegistroProgresionScout.objects.filter(beneficiario__in=get_editable_beneficiarios_qs(user)).distinct()


def get_editable_beneficiarios_qs(user):
    """Beneficiaries whose operational/progression data the actor may manage."""
    if is_full_access(user):
        return Beneficiario.objects.all()
    group_ids = get_responsable_grupo_ids(user)
    unit_ids = get_editable_unidad_ids(user)
    filters = Q(unidad_id__in=unit_ids)
    if group_ids:
        filters |= Q(unidad__grupo_id__in=group_ids)
    return Beneficiario.objects.filter(filters).distinct()


def can_manage_group_data(user, group_id: int) -> bool:
    if is_full_access(user):
        return True
    return group_id in set(get_responsable_grupo_ids(user))


def can_edit_beneficiario(user, beneficiario: Beneficiario) -> bool:
    return get_editable_beneficiarios_qs(user).filter(pk=beneficiario.pk).exists()


def can_manage_beneficiario_progression(user, beneficiario: Beneficiario) -> bool:
    return can_edit_beneficiario(user, beneficiario)


def can_edit_progresion(user, progresion: RegistroProgresionScout) -> bool:
    return can_manage_beneficiario_progression(user, progresion.beneficiario)


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


def can_edit_persona_identity(user, persona: Persona) -> bool:
    """Return whether the actor may edit identity and status fields."""
    if is_full_access(user):
        return True
    return bool(get_persona_group_ids(persona) & set(get_responsable_grupo_ids(user)))


def can_edit_persona_contact(user, persona: Persona) -> bool:
    return can_edit_persona(user, persona)


def can_replace_persona_photo(user, persona: Persona) -> bool:
    return can_edit_persona_contact(user, persona)


def can_view_persona_photo(user, persona: Persona) -> bool:
    """Return whether the actor may download a person's private photo."""
    if is_full_access(user):
        return True

    user_persona = get_user_persona(user)
    if not user_persona:
        return False
    if user_persona.pk == persona.pk:
        return True

    if hasattr(persona, "beneficiario") and hasattr(user_persona, "apoderado"):
        if persona.beneficiario.relaciones_apoderados.filter(apoderado=user_persona.apoderado).exists():
            return True

    return bool(get_persona_group_ids(persona) & set(get_responsable_grupo_ids(user)))


def can_edit_adulto(user, adulto: Adulto) -> bool:
    return is_full_access(user)


def can_download_adulto_certificate(user, adulto: Adulto) -> bool:
    if is_full_access(user):
        return True
    group_ids = set(adulto.asignaciones_unidad.values_list("unidad__grupo_id", flat=True))
    return bool(group_ids & set(get_responsable_grupo_ids(user)))


def can_renew_adulto_certificate(user, adulto: Adulto) -> bool:
    return can_download_adulto_certificate(user, adulto)


def can_reassign_beneficiario(user, beneficiario: Beneficiario, destination: Unidad) -> bool:
    """Return whether the actor may move a beneficiary between assignments."""
    if is_full_access(user):
        return True
    if not beneficiario.unidad_id:
        return False

    source_unit_id = beneficiario.unidad_id
    destination_unit_id = destination.id
    responsable_groups = set(get_responsable_grupo_ids(user))
    if responsable_groups:
        source_group_id = beneficiario.unidad.grupo_id
        if source_group_id in responsable_groups and destination.grupo_id in responsable_groups:
            return True

    editable_unit_ids = set(get_editable_unidad_ids(user))
    return source_unit_id in editable_unit_ids and destination_unit_id in editable_unit_ids


def can_edit_apoderado(user, apoderado: Apoderado) -> bool:
    user_persona = get_user_persona(user)
    return bool(is_full_access(user) or (user_persona and getattr(user_persona, "apoderado", None) == apoderado))


def can_edit_apoderado_committee(user, apoderado: Apoderado) -> bool:
    return is_full_access(user)


def can_edit_unidad(user, unidad: Unidad) -> bool:
    return can_manage_group_data(user, unidad.grupo_id)


def get_persona_detail_permissions(user, persona: Persona) -> dict[str, bool]:
    return {
        "can_edit": can_edit_persona(user, persona),
        "can_edit_identity": can_edit_persona_identity(user, persona),
        "can_edit_contact": can_edit_persona_contact(user, persona),
        "can_replace_photo": can_replace_persona_photo(user, persona),
        "can_download_photo": can_view_persona_photo(user, persona),
    }


def get_adulto_detail_permissions(user, adulto: Adulto) -> dict[str, bool]:
    return {
        "can_edit": can_edit_adulto(user, adulto),
        "can_download_photo": can_view_persona_photo(user, adulto.persona),
        "can_download_certificate": can_download_adulto_certificate(user, adulto),
        "can_renew_certificate": can_renew_adulto_certificate(user, adulto),
    }


def get_beneficiario_detail_permissions(user, beneficiario: Beneficiario) -> dict[str, bool]:
    return {
        "can_edit": can_edit_beneficiario(user, beneficiario),
        "can_download_photo": can_view_persona_photo(user, beneficiario.persona),
        "can_manage_progression": can_manage_beneficiario_progression(user, beneficiario),
        "can_reassign_unit": bool(beneficiario.unidad_id) and (
            is_full_access(user)
            or beneficiario.unidad.grupo_id in set(get_responsable_grupo_ids(user))
            or beneficiario.unidad_id in set(get_editable_unidad_ids(user))
        ),
    }


def get_apoderado_detail_permissions(user, apoderado: Apoderado) -> dict[str, bool]:
    return {
        "can_edit": can_edit_apoderado(user, apoderado),
        "can_download_photo": can_view_persona_photo(user, apoderado.persona),
        "can_edit_committee": can_edit_apoderado_committee(user, apoderado),
    }


def get_unidad_detail_permissions(user, unidad: Unidad) -> dict[str, bool]:
    return {"can_edit": can_edit_unidad(user, unidad)}


def get_persona_group_ids(persona: Persona) -> set[int]:
    group_ids = set()
    if hasattr(persona, "beneficiario") and persona.beneficiario.unidad_id:
        group_ids.add(persona.beneficiario.unidad.grupo_id)
    if hasattr(persona, "adulto"):
        group_ids.update(persona.adulto.asignaciones_unidad.values_list("unidad__grupo_id", flat=True))
    if hasattr(persona, "apoderado"):
        group_ids.update(
            persona.apoderado.relaciones_beneficiarios.exclude(beneficiario__unidad__isnull=True).values_list(
                "beneficiario__unidad__grupo_id", flat=True
            )
        )
    return group_ids


def can_view_expanded_persona_pii(user, persona: Persona) -> bool:
    if is_full_access(user):
        return True
    # Guardians need their own contact data to update it; other unit roles do
    # not gain broader PII merely by viewing their own personnel record.
    if get_user_persona(user) == persona and hasattr(persona, "apoderado"):
        return True
    return bool(get_persona_group_ids(persona) & set(get_responsable_grupo_ids(user)))


def can_view_operational_persona_pii(user, persona: Persona) -> bool:
    if can_view_expanded_persona_pii(user, persona):
        return True
    return bool(
        get_persona_group_ids(persona)
        & set(Unidad.objects.filter(id__in=get_editable_unidad_ids(user)).values_list("grupo_id", flat=True))
    )


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

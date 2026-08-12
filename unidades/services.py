"""Transactional commands for structural unit management."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from catalogos.models import ComposicionPermitida
from personas.models import Adulto, Beneficiario, EstadoPersona, RolAdulto, SexoPersona
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Subgrupo, SubgrupoMiembro, Unidad


def _save(instance, user):
    instance.full_clean()
    instance._history_user = user
    instance.save()
    return instance


def _validate_unit_population(unidad):
    composicion = unidad.composicion_actual()
    activos = Beneficiario.objects.select_for_update().select_related("persona").filter(
        unidad=unidad, persona__estado=EstadoPersona.ACTIVO
    )
    if unidad.cupo_maximo is not None and activos.count() > unidad.cupo_maximo:
        raise ValidationError({"cupo_maximo": "El cupo no puede ser menor que los beneficiarios activos."})
    if composicion == ComposicionPermitida.MIXTA:
        return
    sexo_esperado = SexoPersona.MASCULINO if composicion == ComposicionPermitida.SOLO_HOMBRES else SexoPersona.FEMENINO
    if activos.exclude(persona__sexo=sexo_esperado).exists():
        raise ValidationError({"tipo_composicion": "La composicion no admite a los beneficiarios activos actuales."})
    adultos = AdultoUnidadRol.objects.select_for_update().select_related("adulto__persona").filter(
        unidad=unidad, adulto__persona__estado=EstadoPersona.ACTIVO
    )
    if adultos.exclude(adulto__persona__sexo=sexo_esperado).exists():
        raise ValidationError({"tipo_composicion": "La composicion no admite al equipo adulto actual."})
    if Subgrupo.objects.filter(unidad=unidad, lider_juvenil__persona__sexo__isnull=False).exclude(
        lider_juvenil__persona__sexo=sexo_esperado
    ).exists():
        raise ValidationError({"tipo_composicion": "La composicion no admite a los lideres juveniles actuales."})


@transaction.atomic
def create_unidad(*, user, data):
    unidad = Unidad(**data)
    return _save(unidad, user)


@transaction.atomic
def update_unidad(*, user, unidad, data):
    unidad = Unidad.objects.select_for_update().select_related("rama", "grupo").get(pk=unidad.pk)
    for field, value in data.items():
        setattr(unidad, field, value)
    _validate_unit_population(unidad)
    return _save(unidad, user)


@transaction.atomic
def create_subgrupo(*, user, data):
    if data.get("lider_juvenil"):
        raise ValidationError({"lider_juvenil": "Cree el subgrupo sin lider y asigne primero su membresia."})
    subgrupo = Subgrupo(**data)
    return _save(subgrupo, user)


@transaction.atomic
def update_subgrupo(*, user, subgrupo, data):
    subgrupo = Subgrupo.objects.select_for_update().select_related("unidad").get(pk=subgrupo.pk)
    for field, value in data.items():
        setattr(subgrupo, field, value)
    return _save(subgrupo, user)


@transaction.atomic
def create_subgrupo_miembro(*, user, data):
    subgrupo = Subgrupo.objects.select_for_update().select_related("unidad").get(pk=data["subgrupo"].pk)
    beneficiario = Beneficiario.objects.select_for_update(of=("self",)).select_related(
        "persona", "unidad"
    ).get(pk=data["beneficiario"].pk)
    if subgrupo.unidad.estado != "ACTIVA" or beneficiario.persona.estado != EstadoPersona.ACTIVO:
        raise ValidationError({"subgrupo": "La unidad y el beneficiario deben estar activos."})
    miembro = SubgrupoMiembro(subgrupo=subgrupo, beneficiario=beneficiario)
    return _save(miembro, user)


@transaction.atomic
def reassign_subgrupo_miembro(*, user, miembro, subgrupo):
    source_unidad_id = SubgrupoMiembro.objects.filter(pk=miembro.pk).values_list("subgrupo__unidad_id", flat=True).get()
    destination_unidad_id = Subgrupo.objects.filter(pk=subgrupo.pk).values_list("unidad_id", flat=True).get()
    locked_units = {
        unidad.pk: unidad
        for unidad in Unidad.objects.select_for_update().select_related("grupo", "rama").filter(
            pk__in={source_unidad_id, destination_unidad_id}
        ).order_by("pk")
    }
    miembro = SubgrupoMiembro.objects.select_for_update().select_related(
        "subgrupo__unidad__grupo", "beneficiario__persona"
    ).get(pk=miembro.pk)
    destino = Subgrupo.objects.select_for_update().select_related("unidad__grupo", "unidad__rama").get(pk=subgrupo.pk)
    if miembro.subgrupo.unidad_id != source_unidad_id or destino.unidad_id != destination_unidad_id:
        raise ValidationError({"subgrupo": "La estructura de unidades cambio; vuelva a intentar la reasignacion."})
    source_unidad = locked_units[source_unidad_id]
    destination_unidad = locked_units[destination_unidad_id]
    beneficiario = Beneficiario.objects.select_for_update().select_related("persona").get(pk=miembro.beneficiario_id)
    if beneficiario.subgrupos_liderados.filter(lider_juvenil=beneficiario, lider_juvenil__persona__estado=EstadoPersona.ACTIVO).exists():
        raise ValidationError({"subgrupo": "No se puede reasignar un lider juvenil activo."})
    if destination_unidad.estado != "ACTIVA" or beneficiario.persona.estado != EstadoPersona.ACTIVO:
        raise ValidationError({"subgrupo": "La unidad de destino y el beneficiario deben estar activos."})
    if destination_unidad.cupo_maximo is not None and source_unidad.pk != destination_unidad.pk:
        total = Beneficiario.objects.select_for_update().filter(
            unidad=destination_unidad, persona__estado=EstadoPersona.ACTIVO
        ).count()
        if total >= destination_unidad.cupo_maximo:
            raise ValidationError({"subgrupo": "La unidad de destino no tiene cupos disponibles."})
    beneficiario.unidad = destination_unidad
    beneficiario.rama_actual = destination_unidad.rama
    _save(beneficiario, user)
    miembro.subgrupo = destino
    # ``miembro`` was loaded with its beneficiary relation before the move;
    # replace that cached relation so model validation sees the destination.
    miembro.beneficiario = beneficiario
    _save(miembro, user)
    from organizacion.models import GrupoScout
    for group_id in {source_unidad.grupo_id, destination_unidad.grupo_id}:
        GrupoScout.objects.get(pk=group_id).recalcular_minimo_miembros()
    return miembro


@transaction.atomic
def create_adulto_unidad_rol(*, user, data):
    unidad = Unidad.objects.select_for_update().get(pk=data["unidad"].pk)
    adulto = Adulto.objects.select_for_update().select_related("persona").get(pk=data["adulto"].pk)
    asignaciones = list(AdultoUnidadRol.objects.select_for_update().filter(unidad=unidad))
    if any(asignacion.adulto_id == adulto.pk for asignacion in asignaciones):
        raise ValidationError({"adulto": "El adulto ya tiene una asignacion en esta unidad."})
    if data["rol"] == RolAdultoUnidad.RESPONSABLE and any(
        asignacion.rol == RolAdultoUnidad.RESPONSABLE for asignacion in asignaciones
    ):
        raise ValidationError({"rol": "La unidad ya tiene una persona responsable."})
    try:
        with transaction.atomic():
            asignacion = _save(AdultoUnidadRol(unidad=unidad, adulto=adulto, rol=data["rol"]), user)
    except IntegrityError as exc:
        raise ValidationError({"rol": "No fue posible asignar el rol; la unidad ya tiene una persona responsable."}) from exc

    roles_especiales = {RolAdulto.APODERADO, RolAdulto.RESP_GRUPO, RolAdulto.COLABORADOR}
    if adulto.rol_principal not in roles_especiales:
        if adulto.persona.sexo == SexoPersona.FEMENINO:
            adulto.rol_principal = RolAdulto.GUIA
        elif adulto.persona.sexo == SexoPersona.MASCULINO:
            adulto.rol_principal = RolAdulto.DIRIGENTE
        else:
            return asignacion
        _save(adulto, user)

    return asignacion


@transaction.atomic
def update_adulto_unidad_rol(*, user, asignacion, data):
    unidad_id = AdultoUnidadRol.objects.filter(pk=asignacion.pk).values_list("unidad_id", flat=True).get()
    unidad = Unidad.objects.select_for_update().get(pk=unidad_id)
    asignaciones = list(AdultoUnidadRol.objects.select_for_update().filter(unidad=unidad))
    asignacion = next(item for item in asignaciones if item.pk == asignacion.pk)
    nuevo_rol = data.get("rol", asignacion.rol)
    if asignacion.rol == RolAdultoUnidad.RESPONSABLE and nuevo_rol != asignacion.rol:
        if not any(item.rol == RolAdultoUnidad.RESPONSABLE and item.pk != asignacion.pk for item in asignaciones):
            raise ValidationError({"rol": "No se puede remover al unico responsable de la unidad."})
    if nuevo_rol == RolAdultoUnidad.RESPONSABLE and asignacion.rol != nuevo_rol and any(
        item.rol == RolAdultoUnidad.RESPONSABLE and item.pk != asignacion.pk for item in asignaciones
    ):
        raise ValidationError({"rol": "La unidad ya tiene una persona responsable."})
    asignacion.rol = nuevo_rol
    try:
        with transaction.atomic():
            return _save(asignacion, user)
    except IntegrityError as exc:
        raise ValidationError({"rol": "No fue posible actualizar el rol; la unidad ya tiene una persona responsable."}) from exc

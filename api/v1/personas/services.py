from django.core.exceptions import ValidationError
from django.db import transaction

from personas.models import Adulto, Beneficiario
from unidades.models import SubgrupoMiembro


@transaction.atomic
def renew_adulto_certificate(*, user, adulto: Adulto, data: dict) -> Adulto:
    """Replace an adult certificate and delete the superseded file after commit."""
    adulto = Adulto.objects.select_for_update().select_related("persona").get(pk=adulto.pk)
    previous_file = adulto.certificado_inhabilidades
    previous_name = previous_file.name if previous_file else None

    adulto.certificado_inhabilidades = data["certificado_inhabilidades"]
    adulto.certificado_vigencia_hasta = data["certificado_vigencia_hasta"]
    adulto.full_clean()
    adulto._history_user = user
    adulto.save()

    if previous_name and previous_name != adulto.certificado_inhabilidades.name:
        storage = previous_file.storage
        transaction.on_commit(lambda: storage.delete(previous_name))
    return adulto


@transaction.atomic
def reassign_beneficiario(*, user, beneficiario: Beneficiario, data: dict) -> Beneficiario:
    """Update a beneficiary branch/unit without leaving an invalid subgroup membership."""
    beneficiario = Beneficiario.objects.select_for_update().select_related("persona", "unidad__grupo").get(pk=beneficiario.pk)
    destination = data["unidad"]
    if beneficiario.unidad_id != destination.id and SubgrupoMiembro.objects.filter(beneficiario=beneficiario).exists():
        raise ValidationError({"unidad": "No se puede cambiar la unidad mientras el beneficiario pertenezca a un subgrupo"})
    if beneficiario.unidad_id != destination.id and beneficiario.subgrupos_liderados.exists():
        raise ValidationError({"unidad": "No se puede cambiar la unidad mientras el beneficiario lidere un subgrupo"})

    beneficiario.rama_actual = data["rama_actual"]
    beneficiario.unidad = destination
    beneficiario.full_clean()
    beneficiario._history_user = user
    beneficiario.save()
    return beneficiario

"""Canonical email identity resolution shared by authentication and Persona writes."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q


def normalize_identity_email(value) -> str:
    """Return the case-insensitive, whitespace-free representation of an email."""
    return value.strip().casefold() if isinstance(value, str) else ""


def users_matching_identity_email(email):
    """Return every user that can legitimately claim ``email`` as login identity.

    A linked Persona is authoritative; therefore that user's ``User.email`` is
    deliberately ignored.  ``User.email`` remains authoritative only for users
    without a Persona.
    """
    normalized = normalize_identity_email(email)
    if not normalized:
        return get_user_model().objects.none()

    return get_user_model().objects.filter(
        Q(persona__email__iexact=normalized) | Q(persona__isnull=True, email__iexact=normalized)
    ).distinct()


def resolve_user_by_identity_email(email):
    """Resolve one user, returning ``None`` for absent *or ambiguous* emails."""
    users = list(users_matching_identity_email(email)[:2])
    return users[0] if len(users) == 1 else None


def validate_and_sync_persona_user_email(persona) -> None:
    """Synchronize a linked user's email without creating ambiguous credentials."""
    normalized = normalize_identity_email(persona.email)
    persona.email = normalized
    if not persona.usuario_id or not normalized:
        return

    conflict = users_matching_identity_email(normalized).exclude(pk=persona.usuario_id).exists()
    if conflict:
        raise ValidationError({"email": "El correo ya está asociado a otra cuenta."})

    user = persona.usuario
    if user.email != normalized:
        user.email = normalized
        user.save(update_fields=["email"])

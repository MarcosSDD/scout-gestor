from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from api.v1.access import get_responsable_grupo_ids, get_unidad_roles, get_user_persona
from common.identity import normalize_identity_email, resolve_user_by_identity_email


def serialize_user(user):
    persona = get_user_persona(user)
    unidad_roles = []
    if persona and hasattr(persona, "adulto"):
        unidad_roles = list(get_unidad_roles(user).values("unidad_id", "rol"))

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "persona_id": persona.id if persona else None,
        "responsable_grupo_ids": get_responsable_grupo_ids(user),
        "unidad_roles": unidad_roles,
        "is_apoderado": bool(persona and hasattr(persona, "apoderado")),
    }


class ScoutTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TokenObtainSerializer adds these fields dynamically, so configure
        # them after its initializer to let empty credentials reach the same
        # generic authentication failure as all other bad credentials.
        self.fields["email"].allow_blank = True
        self.fields["password"].allow_blank = True

    def to_internal_value(self, data):
        unexpected_fields = set(data) - {"email", "password"}
        if unexpected_fields:
            raise serializers.ValidationError({"non_field_errors": ["Only email and password are allowed."]})
        return super().to_internal_value(data)

    def validate(self, attrs):
        email = normalize_identity_email(attrs["email"])
        user = resolve_user_by_identity_email(email)
        if not email or user is None or not user.is_active or not user.check_password(attrs["password"]):
            raise AuthenticationFailed(self.error_messages["no_active_account"], "no_active_account")

        self.user = user
        refresh = self.get_token(user)
        data = {"refresh": str(refresh), "access": str(refresh.access_token)}
        data["user"] = serialize_user(self.user)
        return data


class ScoutTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except TokenError as exc:
            raise serializers.ValidationError({"refresh": str(exc)}) from exc


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh = attrs.get("refresh")
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError as exc:
            raise serializers.ValidationError({"refresh": str(exc)}) from exc
        return attrs


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    persona_id = serializers.IntegerField(read_only=True, allow_null=True)
    responsable_grupo_ids = serializers.ListField(read_only=True)
    unidad_roles = serializers.ListField(read_only=True)
    is_apoderado = serializers.BooleanField(read_only=True)

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
    }


class ScoutTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
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

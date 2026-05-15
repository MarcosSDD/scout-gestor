from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.v1.auth.serializers import (
    LogoutSerializer,
    MeSerializer,
    ScoutTokenObtainPairSerializer,
    ScoutTokenRefreshSerializer,
    serialize_user,
)
from api.v1.responses import success_response


class ScoutTokenObtainPairView(TokenObtainPairView):
    serializer_class = ScoutTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(data=serializer.validated_data, message="Token issued")


class ScoutTokenRefreshView(TokenRefreshView):
    serializer_class = ScoutTokenRefreshSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(data=serializer.validated_data, message="Token refreshed")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = MeSerializer(serialize_user(request.user)).data
        return success_response(data=data, message="Authenticated user")


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(data=None, message="Logout successful")

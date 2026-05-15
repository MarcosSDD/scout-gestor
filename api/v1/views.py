from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from api.v1.responses import success_response


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = {
            "status": "ok",
            "version": request.version,
        }
        return success_response(data=data, message="API healthy")


class ProtectedPingView(APIView):
    def get(self, request):
        return success_response(data={"status": "authenticated"}, message="Authenticated")

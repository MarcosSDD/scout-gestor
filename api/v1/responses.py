from rest_framework import status
from rest_framework.response import Response


def success_response(*, data=None, message="OK", meta=None, status_code=status.HTTP_200_OK):
    payload = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status_code)


def error_response(*, message="Error", details=None, code="error", status_code=status.HTTP_400_BAD_REQUEST):
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }
    return Response(payload, status=status_code)

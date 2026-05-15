from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler


def _normalize_details(value):
    if isinstance(value, ErrorDetail):
        return str(value)
    if isinstance(value, list):
        return [_normalize_details(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_details(item) for key, item in value.items()}
    return value


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    details = _normalize_details(response.data)
    message = "Request error"

    if isinstance(details, dict) and "detail" in details and isinstance(details["detail"], str):
        message = details["detail"]

    response.data = {
        "success": False,
        "error": {
            "code": getattr(exc, "default_code", "error"),
            "message": message,
            "details": details,
        },
    }
    response.status_code = response.status_code or status.HTTP_400_BAD_REQUEST
    return response

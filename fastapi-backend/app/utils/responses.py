from typing import Any


def success_response(
    data: Any,
    meta: Any = None
):
    return {
        "success": True,
        "data": data,
        "meta": meta
    }


def error_response(
    code: str,
    message: str,
    details: list[Any] | None = None
):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or []
        }
    }

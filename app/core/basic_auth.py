from __future__ import annotations

import base64
import hmac

from fastapi import Request
from fastapi.responses import Response

from app.core.config import settings


def is_basic_auth_allowed(request: Request) -> bool:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Basic "):
        return False

    try:
        decoded = base64.b64decode(authorization[6:]).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False

    if ":" not in decoded:
        return False

    username, password = decoded.split(":", 1)
    return hmac.compare_digest(username, settings.basic_auth_username) and hmac.compare_digest(password, settings.basic_auth_password)


def basic_auth_challenge() -> Response:
    return Response(
        content="Authentication required",
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="shipment_planner"'},
    )

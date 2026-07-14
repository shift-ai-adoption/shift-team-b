"""Basic auth middleware (requirement: ID admin / pass admin123!)."""
import base64
import os
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

USER = os.environ.get("BASIC_AUTH_USER", "admin")
PASS = os.environ.get("BASIC_AUTH_PASS", "admin123!")

EXEMPT_PATHS = {"/api/health"}


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS or request.method == "OPTIONS":
            return await call_next(request)
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth[6:]).decode("utf-8")
                user, _, password = decoded.partition(":")
                if (secrets.compare_digest(user, USER)
                        and secrets.compare_digest(password, PASS)):
                    return await call_next(request)
            except Exception:
                pass
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"},
            headers={"WWW-Authenticate": 'Basic realm="RAG System"'},
        )

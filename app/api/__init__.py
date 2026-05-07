"""
API Blueprint

Contract:
- Base prefix: /api
- Unified envelope: {"data": <payload>|null, "error": {"code": str, "message": str}|null}
- Errors are always JSON via global handlers.

Notes for Swagger:
- Some swagger examples show raw JSON. Actual responses are wrapped in the envelope above.
"""

import warnings

from flask import Blueprint, jsonify
from app.services.errors import UnauthorizedError
from app.services.responses import OkResult

bp = Blueprint("api", __name__, url_prefix="/api")

# ---------------------------------------------------------------------------
# Global authentication enforcement
#
# The following before_request hook enforces that all API endpoints (except
# authentication and health-check routes) require a valid session token.
# The token is retrieved from either the ``auth_token`` cookie or the
# ``Authorization`` header. If the token is missing or invalid, the
# request is short-circuited with a 401 response. Upon successful
# validation the user object is stored in ``flask.g.current_user`` for
# downstream handlers.  This ensures a consistent security model
# across the application and avoids duplicating authentication logic
# within every route.
#
# Endpoints beginning with /api/auth or /api/health are exempted from
# authentication to allow login, registration and liveness probes.
from flask import request, g, current_app

PUBLIC_API_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/verify",
    "/api/auth/logout",
    "/api/auth/google",
    "/api/health",
}


def extract_auth_token() -> str | None:
    """Extract the session token from cookie or Authorization header."""
    header = request.headers.get("Authorization", "").strip()
    if header.lower().startswith("bearer "):
        header = header[7:].strip()
    return request.cookies.get("auth_token") or header or None


@bp.before_request
def _enforce_authentication():
    """Require authentication for most API endpoints.

    This hook runs before each request to the API blueprint. It skips
    authentication for paths under /api/auth (login, register, Google login,
    verify, logout) and the health-check endpoint. For all other paths it
    resolves the current user via the configured ``auth_service``.
    If the token is invalid or missing a JSON response with code
    ``unauthenticated`` is returned.
    """
    # Normalise the request path relative to the blueprint
    path = request.path
    # Skip auth routes and health check
    if path in PUBLIC_API_PATHS:
        return None
    auth_service = current_app.extensions.get("auth_service")
    token = extract_auth_token()
    user = auth_service.verify_token(token) if token else None
    if user is None:
        raise UnauthorizedError(
            "Authentication required",
            code="unauthenticated",
        )
    # Attach user to request context for downstream handlers
    g.current_user = user
    return None


def make_response(data=None, error=None, status=200):
    """
    Deprecated unified API response helper.

    Deprecated:
    - Use service-layer result objects such as ``OkResult`` or ``CreatedResult``.
    - Return ``result.to_flask_response()`` from the route.
    - Raise ``BadRequestError`` / ``NotFoundError`` from the service layer for
      error cases instead of building manual error responses in the route.

    Returns:
      JSON:
        {
          "data": any or null,
          "error": {"code": str, "message": str} or null
        }
    """
    warnings.warn(
        "app.api.make_response is deprecated. "
        "Use `from app.services.responses import OkResult` (or another result "
        "object such as CreatedResult) and return "
        "`result.to_flask_response()` from the route. For failures, raise "
        "`BadRequestError` or `NotFoundError` from the service layer instead "
        "of building manual error responses.",
        DeprecationWarning,
        stacklevel=2,
    )
    return jsonify({"data": data, "error": error}), status


@bp.route("/health", methods=["GET"], strict_slashes=False)
def health():
    """
    GET /api/health
    Summary: Liveness probe

    Responses:
      200:
        data:
          {
            "status": "ok"
          }
        error: null
    """
    return OkResult({"status": "ok"}).to_flask_response()

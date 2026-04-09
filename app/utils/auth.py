"""
Authentication utilities and decorators.

This module defines helper functions and decorators used to require
authentication for API endpoints. The ``login_required`` decorator
verifies a client-provided session token (via cookie or Authorization
header) using the configured :class:`app.services.auth_service.AuthService`.
If the token is valid, the current user is attached to
``flask.g.current_user`` for use within the request context.
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Any, TypeVar, cast

from flask import current_app, g

from app.api import make_response, extract_auth_token

F = TypeVar("F", bound=Callable[..., Any])


def login_required(f: F) -> F:
    """Decorator to enforce authentication on a view.

    The decorator extracts the session token from either the
    ``auth_token`` cookie or the ``Authorization`` header. It uses the
    configured authentication service to validate the token. If the
    token is missing or invalid, a 401 response is returned using the
    unified API format. When valid, the resolved user is attached to
    ``flask.g.current_user`` and the original view is invoked.

    Returns:
        The decorated view function.
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any):
        auth_service = current_app.extensions.get("auth_service")
        token = extract_auth_token()
        user = auth_service.verify_token(token) if token else None
        if user is None:
            return make_response(None, {"code": "unauthenticated", "message": "Authentication required"}, 401)
        # Attach user to request context for downstream handlers
        g.current_user = user
        return f(*args, **kwargs)

    return cast(F, wrapper)

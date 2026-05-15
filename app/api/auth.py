"""
Auth API

This module exposes endpoints for user authentication and registration.
It provides JSON-only routes for logging in, registering a new account,
verifying an email address, and logging out. Responses always use the
unified API envelope defined in :mod:`app.api` and issue/consume
authentication tokens via HTTP cookies.

Paths:
  - POST /api/auth/login
  - POST /api/auth/register
  - POST /api/auth/verify
  - POST /api/auth/logout

Notes:
- The client must send at minimum an ``email`` and ``password`` for
  registration and login. Additional fields are ignored.
- Upon successful login, an opaque session token is returned to the
  client via a ``Set-Cookie`` header (`auth_token`). Clients must
  include this cookie on subsequent authenticated requests.
- During registration, a verification code is generated and sent to
  the supplied email address. In development and test environments,
  the user is automatically verified to simplify local testing. A
  separate verification endpoint is provided for production flows.
"""

from flask import request, current_app, g
from app.api import bp, extract_auth_token
from app.api.request_parsing import parse_json_object_body
from app.services.errors import BadRequestError, UnauthorizedError
from app.services.responses import CreatedResult, OkResult
import requests
from app.utils.auth import login_required


def _auth_service():
    """Convenience accessor for the authentication service."""
    return current_app.extensions.get("auth_service")


def _cookie_secure() -> bool:
    return bool(current_app.config.get("SESSION_COOKIE_SECURE") or request.is_secure)


@bp.post("/auth/login", strict_slashes=False)
def api_login():
    """
    POST /api/auth/login
    Summary: User login

    Request:
      {"email":"user@example.com","password":"***"}

    Responses:
      200: {"data":{"ok":true}, "error":null}
      401: {"data":null,"error":{"code":"auth_failed","message":"Invalid credentials"}}
    """
    p = parse_json_object_body()
    email = (p.get("email") or "").strip()
    password = p.get("password", "")
    # Authenticate via the auth service; it raises on failure.
    token = _auth_service().login(email, password)
    resp, status_code = OkResult({"ok": True}).to_flask_response()
    # Use a long-lived, HTTP-only cookie; SameSite=Lax allows inclusion on same-site requests
    resp.set_cookie(
        "auth_token",
        token,
        httponly=True,
        samesite="Lax",
        max_age=_auth_service().TOKEN_LIFETIME,
        path="/",
        secure=_cookie_secure(),
    )
    return resp


@bp.post("/auth/register", strict_slashes=False)
def api_register():
    """
    POST /api/auth/register
    Summary: User registration

    Request:
      {"email":"user@example.com","password":"***"}

    Responses:
      201: {"data":{"created":true,"id":"<uuid>"},"error":null}
      400: {"data":null,"error":{"code":"bad_request","message":"email and password required"}}
      409: {"data":null,"error":{"code":"exists","message":"User already exists"}}
    """
    p = parse_json_object_body()
    email = (p.get("email") or "").strip()
    password = p.get("password", "")
    user, _code = _auth_service().register_user(email, password)
    return CreatedResult({"created": True, "id": str(user.id)}).to_flask_response()


@bp.post("/auth/verify", strict_slashes=False)
def api_verify_email():
    """
    POST /api/auth/verify
    Summary: Verify email address using a confirmation code

    Request:
      {"email": "user@example.com", "code": "123456"}

    Responses:
      200: {"data": {"verified": true}, "error": null}
      400/404: appropriate error code

    On success the user's ``is_verified`` flag is set and the code is
    marked as used. Subsequent login attempts will then succeed.
    """
    p = parse_json_object_body()
    email = (p.get("email") or "").strip()
    code = (p.get("code") or "").strip()
    if not email or not code:
        raise BadRequestError("email and code required")
    ok = _auth_service().verify_email_code(email, code)
    if not ok:
        raise BadRequestError("Invalid or expired code", code="invalid_code")
    return OkResult({"verified": True}).to_flask_response()


@bp.get("/auth/me", strict_slashes=False)
@login_required
def api_auth_me():
    """Return the currently authenticated user."""
    user = g.current_user
    return OkResult(
        {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_verified": bool(user.is_verified),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    ).to_flask_response()


@bp.post("/auth/logout", strict_slashes=False)
def api_logout():
    token = extract_auth_token()
    if token:
        _auth_service().logout(token)
    resp, _status_code = OkResult({"ok": True}).to_flask_response()
    # Remove the cookie regardless of whether it existed
    resp.set_cookie(
        "auth_token",
        "",
        expires=0,
        max_age=0,
        path="/",
        httponly=True,
        samesite="Lax",
        secure=_cookie_secure(),
    )
    return resp


# ----------------------------------------------------------------------
# Google OAuth login endpoint
# ----------------------------------------------------------------------
@bp.post("/auth/google", strict_slashes=False)
def api_login_google():
    """
    POST /api/auth/google
    Summary: Log in or register a user via Google OAuth

    Request:
      {"token": "<google id_token>"}

    Responses:
      200: {"data": {"ok": true}, "error": null}
      400/401: Appropriate error codes for missing or invalid token

    This endpoint accepts an ID token obtained from Google Sign-In on the
    client. It verifies the token using Google's tokeninfo endpoint,
    extracts the email address, and either logs in an existing user or
    creates a new one. A session token is returned via the
    ``Set-Cookie`` header on success.
    """
    payload = parse_json_object_body()
    id_token = (payload.get("token") or payload.get("id_token") or "").strip()
    if not id_token:
        raise BadRequestError("token required")
    # Call Google's tokeninfo endpoint to validate the token. According to
    # Google documentation, this endpoint returns the decoded claims if the
    # token is valid and has not expired. See:
    # https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
    try:
        verify_resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
            timeout=5,
        )
        if verify_resp.status_code != 200:
            raise UnauthorizedError("Invalid Google token", code="auth_failed")
        claims = verify_resp.json()
    except Exception:
        raise UnauthorizedError("Failed to verify Google token", code="auth_failed")
    # Ensure the token is intended for our application
    aud = claims.get("aud") or claims.get("azp")  # Some responses use "azp"
    client_id_expected = current_app.config.get("GOOGLE_CLIENT_ID")
    if client_id_expected and aud != client_id_expected:
        raise UnauthorizedError("Token audience mismatch", code="auth_failed")
    email = claims.get("email")
    email_verified = claims.get("email_verified")
    if not email or str(email_verified).lower() not in {"true", "1"}:
        raise UnauthorizedError("Email not verified", code="auth_failed")
    # Delegate to the auth service to log in or create the user
    token = _auth_service().login_with_google(email)
    if not token:
        raise UnauthorizedError("Unable to authenticate user", code="auth_failed")
    resp, _status_code = OkResult({"ok": True}).to_flask_response()
    resp.set_cookie(
        "auth_token",
        token,
        httponly=True,
        samesite="Lax",
        max_age=_auth_service().TOKEN_LIFETIME,
        path="/",
        secure=_cookie_secure(),
    )
    return resp

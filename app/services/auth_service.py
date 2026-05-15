"""
Authentication and registration service.

This module provides a concrete implementation for authenticating
against the database-backed user model. It replaces the previous
in-memory stub and introduces token-based sessions and optional email
verification. The service is designed to be stateless from the
client's perspective: clients authenticate by presenting an opaque
token via a cookie or Authorization header, and the service resolves
that token into a user. Tokens are persisted in the database so that
they can be invalidated on logout.
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models import User, AuthToken, EmailVerification
from app.services.errors import BadRequestError, ConflictError, UnauthorizedError
from app.services.users_service import create_user_with_main_account


class AuthService:
    """Authentication service backed by the database.

    The service handles user creation, password hashing and checking,
    issuing and revoking session tokens, and generating/verifying
    one-time email confirmation codes. It does not store any state in
    the Flask session; instead, all persistent session information is
    stored in the `auth_tokens` table. Clients authenticate by sending
    the issued token back to the server on each request.
    """

    # Default token lifetime in seconds (7 days)
    TOKEN_LIFETIME = 60 * 60 * 24 * 7
    # Email verification code lifetime in minutes
    VERIFICATION_LIFETIME = 60 * 24  # 1 day

    def __init__(self, app):
        self.app = app

    # ------------------------------------------------------------------
    # Password utilities
    # ------------------------------------------------------------------
    def hash_password(self, raw: str) -> str:
        """Return a hashed representation of the provided password."""
        return generate_password_hash(raw)

    def verify_password(self, raw: str, hashed: str) -> bool:
        """Check a password against its hashed representation."""
        return check_password_hash(hashed, raw)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def _derive_username(self, email: str) -> str:
        """Derive a username from an email address.

        If the local part of the email is already taken, append a random
        suffix until a unique username is found. This logic is
        deterministic for most users but avoids collisions.
        """
        local_part = (email or "").split("@")[0]
        base = local_part[:32] if local_part else "user"
        username = base
        i = 1
        while db.session.execute(db.select(User).filter_by(username=username)).scalar() is not None:
            suffix = f"{i}"
            username = (base + suffix)[:32]
            i += 1
        return username

    def register_user(self, email: str, password: str) -> Tuple[User, str]:
        """Create a new user and send a verification code.

        Returns a tuple of the newly created user and the verification
        code. A verification code is always generated and persisted in
        the database, even if the environment automatically verifies
        accounts. Callers may ignore the code if they plan to defer
        verification to a separate step.

        Raises:
            BadRequestError: If email or password is missing.
            ConflictError: If the user already exists.
        """
        email_normalized = (email or "").strip().lower()
        if not email_normalized or not password:
            raise BadRequestError("email and password required")
        # Check existence
        existing = db.session.execute(db.select(User).filter_by(email=email_normalized)).scalar()
        if existing is not None:
            raise ConflictError("User already exists", code="exists")
        username = self._derive_username(email_normalized)
        user = create_user_with_main_account(
            username=username,
            email=email_normalized,
            password_hash=self.hash_password(password),
            is_verified=False,
            currency="EUR",
        )
        # Always generate a verification code
        code = self._generate_verification_code()
        expires = datetime.now(timezone.utc) + timedelta(minutes=self.VERIFICATION_LIFETIME)
        ver = EmailVerification(user_id=user.id, code=code, expires_at=expires, is_used=False)
        db.session.add(ver)
        # Auto-verify user in test/dev environments to simplify tests
        if self.app.config.get("TESTING") or self.app.config.get("DEBUG"):
            user.is_verified = True
            ver.is_used = True
        db.session.commit()
        # Attempt to send code via email
        self._send_verification_email(email_normalized, code)
        return user, code

    # ------------------------------------------------------------------
    # Login / Logout
    # ------------------------------------------------------------------
    def login(self, email: str, password: str) -> str:
        """Authenticate a user and issue a new token.

        Returns the opaque token string if authentication succeeds.
        Only verified users can obtain tokens.

        Raises:
            UnauthorizedError: If the credentials are invalid or the
            account has not been verified yet.
        """
        email_normalized = (email or "").strip().lower()
        if not email_normalized or not password:
            raise UnauthorizedError(
                "Invalid credentials or account not verified",
                code="auth_failed",
            )
        user = db.session.execute(db.select(User).filter_by(email=email_normalized)).scalar()
        if user is None:
            raise UnauthorizedError(
                "Invalid credentials or account not verified",
                code="auth_failed",
            )
        # Must be verified to login
        if not user.is_verified:
            raise UnauthorizedError(
                "Invalid credentials or account not verified",
                code="auth_failed",
            )
        if not self.verify_password(password, user.password_hash):
            raise UnauthorizedError(
                "Invalid credentials or account not verified",
                code="auth_failed",
            )
        # Generate a unique token
        token_value = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.TOKEN_LIFETIME)
        token = AuthToken(user_id=user.id, token=token_value, expires_at=expires_at)
        db.session.add(token)
        db.session.commit()
        return token_value

    def logout(self, token_str: str) -> None:
        """Invalidate a token by deleting it from the database."""
        if not token_str:
            return
        tok = db.session.execute(db.select(AuthToken).filter_by(token=token_str)).scalar()
        if tok is not None:
            db.session.delete(tok)
            db.session.commit()

    def verify_token(self, token_str: str) -> Optional[User]:
        """Look up and validate a token.

        Returns the associated user if the token exists and is not
        expired; otherwise returns None.
        """
        if not token_str:
            return None
        tok = db.session.execute(db.select(AuthToken).filter_by(token=token_str)).scalar()
        if tok is None:
            return None
        if tok.is_expired():
            # Clean up expired token
            db.session.delete(tok)
            db.session.commit()
            return None
        return tok.user

    # ------------------------------------------------------------------
    # Email verification
    # ------------------------------------------------------------------
    def verify_email_code(self, email: str, code: str) -> bool:
        """Validate a verification code for a given email.

        If the code is valid, marks the user as verified and the code as
        used. Returns True on success, False otherwise. Expired or
        already-used codes are considered invalid. If multiple codes
        exist for the user, this method checks all unused codes.
        """
        email_normalized = (email or "").strip().lower()
        if not email_normalized or not code:
            return False
        user = db.session.execute(db.select(User).filter_by(email=email_normalized)).scalar()
        if user is None:
            return False
        if user.is_verified:
            return True
        codes = (
            db.session.execute(
                db.select(EmailVerification)
                .filter_by(user_id=user.id, is_used=False)
            ).scalars().all()
        )
        for ver in codes:
            if ver.code == code and not ver.is_expired():
                ver.is_used = True
                user.is_verified = True
                db.session.commit()
                return True
        return False

    # ------------------------------------------------------------------
    # Google OAuth login
    # ------------------------------------------------------------------
    def login_with_google(self, email: str) -> Optional[str]:
        """
        Authenticate or create a user using a verified Google email address.

        This helper is used by the Google OAuth endpoint to either
        authenticate an existing account or create a new one when a user
        logs in with their Google account. The provided email must be
        verified by Google prior to invoking this method.

        Args:
            email (str): The Google account's email address (normalized to lower-case).

        Returns:
            Optional[str]: A newly issued opaque session token if the login
            succeeds. Returns ``None`` if the email is missing or some
            unexpected error occurs.
        """
        email_normalized = (email or "").strip().lower()
        if not email_normalized:
            return None
        # Look up existing user by email
        user = db.session.execute(db.select(User).filter_by(email=email_normalized)).scalar()
        if user is None:
            # Create a new user record. Use the local part of the email as the
            # base for the username and ensure uniqueness. Because the user
            # authenticated via Google, we mark them as verified and assign a
            # random password hash to satisfy the non-null constraint. The
            # password will not be used for login and can be reset later.
            username = self._derive_username(email_normalized)
            random_password = secrets.token_urlsafe(16)
            password_hash = self.hash_password(random_password)
            user = create_user_with_main_account(
                username=username,
                email=email_normalized,
                password_hash=password_hash,
                is_verified=True,
                currency="EUR",
            )
        else:
            # For an existing user, ensure the account is marked as verified.
            if not user.is_verified:
                user.is_verified = True
        # Issue a new session token, similar to the normal login flow
        token_value = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.TOKEN_LIFETIME)
        token = AuthToken(user_id=user.id, token=token_value, expires_at=expires_at)
        db.session.add(token)
        db.session.commit()
        return token_value

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_verification_code(self) -> str:
        """Generate a numeric or alphanumeric verification code."""
        # Simple 6-digit numeric code
        return f"{secrets.randbelow(10**6):06d}"

    def _send_verification_email(self, to_email: str, code: str) -> None:
        """
        Send the verification code to the user's email address.

        In production the SMTP settings can be configured via
        environment variables (`SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`,
        `SMTP_PASSWORD`). If these variables are not defined or the
        server cannot be reached, the code will simply be logged to
        standard output. This allows registration to proceed locally
        without requiring a mail server.
        """
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", "0")) if os.getenv("SMTP_PORT") else None
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        subject = "Your verification code"
        body = f"Hello,\n\nYour verification code is: {code}\n\n"
        # If SMTP settings are incomplete, just print the code
        if not smtp_server or not smtp_port or not smtp_user or not smtp_password:
            current_app.logger.info(
                "Skipping email send; incomplete SMTP configuration. Verification code for %s: %s",
                to_email,
                code,
            )
            return
        try:
            import smtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = to_email
            msg.set_content(body)
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        except Exception as exc:
            current_app.logger.warning(
                "Failed to send verification email to %s: %s. Code: %s",
                to_email,
                exc,
                code,
            )

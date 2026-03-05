import os
from .repository_inmemory import build_services
from .qr_parser_stub import QrParserStub
from .ekasa_client_stub import EkasaClientStub
from .export_stub import ExportServiceStub
from .auth_service import AuthService

def init_services(app):
    """
    Initialise all business services.

    This function constructs the in-memory repositories for transactions,
    budgets, and goals, then attaches stub implementations for
    non-persistent external services (QR parsing, eKasa client, export).
    It also instantiates the concrete AuthService to handle user
    registration and authentication against the database. Both the
    container of in-memory services and the AuthService instance are
    stored on the Flask application for later retrieval.
    """
    # Build repositories and optional seed data. Pass through any test
    # user configuration unchanged so that test harnesses can create
    # domain users for non-auth logic. Note that authentication does not
    # rely on this in-memory user repository; real users reside in the
    # database.
    test_email = os.getenv("TEST_USER_EMAIL")
    test_password_raw = os.getenv("TEST_USER_PASSWORD")
    test_password_hash = None
    if test_password_raw:
        # Use a temporary AuthService instance solely for hashing; do not
        # store this stub anywhere else.
        temp_auth = AuthService(app)
        test_password_hash = temp_auth.hash_password(test_password_raw)
    elif os.getenv("TEST_USER_PASSWORD_HASH"):
        test_password_hash = os.getenv("TEST_USER_PASSWORD_HASH")
    container = build_services(
        os.getenv("IMPORT_XLSX_PATH"),
        app.config.get("DEFAULT_CURRENCY", "EUR"),
        test_email,
        test_password_hash,
    )
    # Attach stubbed external service implementations
    container.qr_parser = QrParserStub()
    container.ekasa = EkasaClientStub()
    container.export = ExportServiceStub(container.transactions)
    # Instantiate the real authentication service
    auth_service = AuthService(app)
    container.auth = auth_service
    # Expose services and auth service on the Flask app
    app.extensions["services"] = container
    app.extensions["auth_service"] = auth_service
    return container

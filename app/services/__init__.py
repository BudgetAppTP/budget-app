import os
from .repository_inmemory import build_services
from .qr_parser_stub import QrParserStub
from .ekasa_client_stub import EkasaClientStub
from .export_stub import ExportServiceStub
from .auth_stub import AuthServiceStub

def init_services(app):
    email = os.getenv("TEST_USER_EMAIL")
    pwd_raw = os.getenv("TEST_USER_PASSWORD")
    auth = AuthServiceStub()
    pwd_hash = auth.hash_password(pwd_raw) if pwd_raw else os.getenv("TEST_USER_PASSWORD_HASH")
    container = build_services(os.getenv("IMPORT_XLSX_PATH"), app.config.get("DEFAULT_CURRENCY", "EUR"), email, pwd_hash)
    container.qr_parser = QrParserStub()
    container.ekasa = EkasaClientStub()
    container.export = ExportServiceStub(container.transactions)
    container.auth = auth
    app.extensions["services"] = container
    return container

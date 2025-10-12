import os
from .repository_inmemory import build_services

def init_services(app):
    email = os.getenv("TEST_USER_EMAIL")
    pwd_hash = os.getenv("TEST_USER_PASSWORD_HASH") or os.getenv("TEST_USER_PASSWORD")
    container = build_services(os.getenv("IMPORT_XLSX_PATH"), app.config.get("DEFAULT_CURRENCY", "EUR"), email, pwd_hash)
    app.extensions["services"] = container
    return container

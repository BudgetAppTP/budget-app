import os

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    WTF_CSRF_ENABLED = os.getenv("WTF_CSRF_ENABLED", "true").lower() == "true"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    TESTING = False
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "EUR")
    IMPORT_XLSX_PATH = os.getenv("IMPORT_XLSX_PATH", "/mnt/data/BugetAppTP.xlsx")

    SWAGGER_URL = "/api/docs"
    API_URL = "/static/swagger.json"

class DevConfig(BaseConfig):
    DEBUG = True

class TestConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False

class ProdConfig(BaseConfig):
    DEBUG = False

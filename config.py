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

    # Use a SQLite database stored inside the Flask instance directory.
    # The file will be created at: <project_root>/instance/dev.db
    SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"


class TestConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProdConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:password@localhost/mydb"
    )

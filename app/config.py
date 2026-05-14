import os

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    WTF_CSRF_ENABLED = False
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    TESTING = False
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "EUR")
    IMPORT_XLSX_PATH = os.getenv("IMPORT_XLSX_PATH", "/mnt/data/BugetAppTP.xlsx")
    MAX_SAVINGS_FUNDS = int(os.getenv("MAX_SAVINGS_FUNDS", "10"))

    # Google OAuth configuration. Set ``GOOGLE_CLIENT_ID`` to the client ID
    # obtained from the Google Developer Console. When provided, the
    # application will validate ID tokens sent from the client against this
    # value. See https://developers.google.com/identity/sign-in/web/sign-in
    # for details on obtaining a client ID.
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

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
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://budget:budget@db:5432/budget"
    )


class LocalDockerConfig(BaseConfig):
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://budget:budget@db:5432/budget"
    )

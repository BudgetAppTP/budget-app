import os
import sqlite3
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.extensions import db, migrate
from app.services.errors import ServiceError
from app.services import init_auth_service, init_qr_service

load_dotenv()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(config_object=None):
    flask_app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder=None,
    )

    CORS(flask_app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    if config_object:
        flask_app.config.from_object(config_object)
    else:
        app_env = os.getenv("APP_ENV", "development").lower()
        if app_env == "production":
            from app.config import ProdConfig as Cfg
        elif app_env == "test":
            from app.config import TestConfig as Cfg
        elif app_env == "docker-local":
            from app.config import LocalDockerConfig as Cfg
        else:
            from app.config import DevConfig as Cfg
        flask_app.config.from_object(Cfg)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    init_auth_service(flask_app)
    init_qr_service(flask_app)

    with flask_app.app_context():
        import app.models
        if flask_app.config.get("DEBUG") or flask_app.config.get("TESTING"):
            app.models.Base.metadata.create_all(bind=db.engine)

    _register_error_handlers(flask_app)
    _register_swagger(flask_app)
    _register_api(flask_app)
    _register_legacy_guard(flask_app)

    return flask_app


def _register_api(flask_app: Flask):
    from app.api import bp as api_bp
    import app.api.auth          # noqa: F401
    import app.api.account       # noqa: F401
    import app.api.goals         # noqa: F401
    import app.api.savings_funds # noqa: F401
    import app.api.allocations   # noqa: F401
    import app.api.importqr      # noqa: F401
    import app.api.export        # noqa: F401
    import app.api.dashboard     # noqa: F401
    import app.api.incomes       # noqa: F401
    import app.api.receipts      # noqa: F401
    import app.api.receipt_items # noqa: F401
    import app.api.users         # noqa: F401
    import app.api.tags          # noqa: F401
    import app.api.monthly_budget # noqa: F401
    import app.api.categories    # noqa: F401
    import app.api.analytics     # noqa: F401
    flask_app.register_blueprint(api_bp)


def _register_swagger(flask_app: Flask):
    swaggerui_bp = get_swaggerui_blueprint(
        flask_app.config["SWAGGER_URL"],
        flask_app.config["API_URL"],
        config={"app_name": "Budget API"},
    )
    flask_app.register_blueprint(swaggerui_bp, url_prefix=flask_app.config["SWAGGER_URL"])



def _register_error_handlers(flask_app: Flask):
    @flask_app.errorhandler(ServiceError)
    def handle_service_error(e: ServiceError):
        return e.to_flask_response()

    @flask_app.errorhandler(HTTPException)
    def handle_http_error(e):
        error = ServiceError(message=e.description, code=str(e.code), status_code=e.code)
        return error.to_flask_response()

    @flask_app.errorhandler(Exception)
    def handle_unexpected_error(e):
        flask_app.logger.exception(e)
        return ServiceError().to_flask_response()


def _register_legacy_guard(flask_app: Flask):
    try:
        from .legacy_guard import register_legacy_guard as _rg
        _rg(flask_app)
    except Exception:
        pass

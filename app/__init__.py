import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
from flask_swagger_ui import get_swaggerui_blueprint

from app.extensions import db, migrate
from app.services import init_services

load_dotenv()


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
            from config import ProdConfig as Cfg
        elif app_env == "test":
            from config import TestConfig as Cfg
        else:
            from config import DevConfig as Cfg
        flask_app.config.from_object(Cfg)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    init_services(flask_app)

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
    import app.api.transactions  # noqa: F401
    import app.api.budgets       # noqa: F401
    import app.api.goals         # noqa: F401
    import app.api.importqr      # noqa: F401
    import app.api.export        # noqa: F401
    import app.api.dashboard     # noqa: F401
    import app.api.incomes       # noqa: F401
    import app.api.receipts      # noqa: F401
    import app.api.receipt_items # noqa: F401
    import app.api.users         # noqa: F401
    import app.api.tags          # noqa: F401
    import app.api.monthly_budget # noqa: F401
    flask_app.register_blueprint(api_bp)


def _register_swagger(flask_app: Flask):
    swaggerui_bp = get_swaggerui_blueprint(
        flask_app.config["SWAGGER_URL"],
        flask_app.config["API_URL"],
        config={"app_name": "Budget API"},
    )
    flask_app.register_blueprint(swaggerui_bp, url_prefix=flask_app.config["SWAGGER_URL"])



def _register_error_handlers(flask_app: Flask):
    @flask_app.errorhandler(HTTPException)
    def handle_http_error(e):
        return jsonify({"data": None, "error": {"code": str(e.code), "message": e.description}}), e.code

    @flask_app.errorhandler(Exception)
    def handle_unexpected_error(e):
        flask_app.logger.exception(e)
        return jsonify({"data": None, "error": {"code": "internal_error", "message": "Internal Server Error"}}), 500


def _register_legacy_guard(flask_app: Flask):
    try:
        from .legacy_guard import register_legacy_guard as _rg
        _rg(flask_app)
    except Exception:
        pass

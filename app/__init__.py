import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from app.extensions import db

from app.services import init_services
from flask_swagger_ui import get_swaggerui_blueprint


load_dotenv()


def register_blueprints(flask_app):
    """Register all blueprints dynamically."""
    from importlib import import_module

    blueprint_modules = [
        "app.blueprints.dashboard",
        "app.blueprints.transactions",
        "app.blueprints.budgets",
        "app.blueprints.goals",
        "app.blueprints.importqr",
        "app.blueprints.auth",
        "app.blueprints.export",
        "app.blueprints.receipts",
        "app.blueprints.incomes",
        "app.blueprints.needs",
        "app.blueprints.users",
    ]

    for module_path in blueprint_modules:
        module = import_module(module_path)
        flask_app.register_blueprint(module.bp)

    swaggerui_blueprint = get_swaggerui_blueprint(
        flask_app.config["SWAGGER_URL"],
        flask_app.config["API_URL"],
        config={"app_name": "Receipts API"}
    )

    flask_app.register_blueprint(swaggerui_blueprint, url_prefix=flask_app.config["SWAGGER_URL"])


def create_app(config_object=None):
    flask_app = Flask(__name__, instance_relative_config=True)

    CORS(flask_app, resources={r"/api/*": {"origins": "*"}})

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
    init_services(flask_app)

    with flask_app.app_context():
        import app.models

        if flask_app.config.get("DEBUG") or flask_app.config.get("TESTING"):
            app.models.Base.metadata.create_all(bind=db.engine)

    register_blueprints(flask_app)
    return flask_app

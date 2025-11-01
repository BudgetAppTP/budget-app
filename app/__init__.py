import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException

load_dotenv()

def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)

    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173"]}}, supports_credentials=True)

    if config_object:
        app.config.from_object(config_object)
    else:
        env = os.getenv("APP_ENV", "development").lower()
        if env == "production":
            from config import ProdConfig as Cfg
        elif env == "test":
            from config import TestConfig as Cfg
        else:
            from config import DevConfig as Cfg
        app.config.from_object(Cfg)

    register_error_handlers(app)
    register_blueprints(app)
    return app

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return jsonify({"data": None, "error": {"code": str(e.code), "message": e.description}}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.exception(e)
        return jsonify({"data": None, "error": {"code": "internal_error", "message": "Internal Server Error"}}), 500

def register_blueprints(app):
    from app.api import bp as api_bp
    import app.api.auth      # noqa
    import app.api.transactions  # noqa
    import app.api.budgets       # noqa
    import app.api.goals         # noqa
    import app.api.importqr      # noqa
    app.register_blueprint(api_bp)

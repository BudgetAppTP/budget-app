import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
from .legacy_guard import register_legacy_guard

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
    register_legacy_guard(app)
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
    import app.api.auth
    import app.api.transactions
    import app.api.budgets
    import app.api.goals
    import app.api.importqr
    import app.api.export
    import app.api.dashboard
    import app.api.incomes
    import app.api.receipts
    import app.api.receipt_items
    import app.api.users
    app.register_blueprint(api_bp)

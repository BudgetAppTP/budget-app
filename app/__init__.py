from flask import Flask
from flask_cors import CORS
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
import os
from app.services import init_services
from flask_swagger_ui import get_swaggerui_blueprint

csrf = CSRFProtect()

def create_app(config_object=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    if config_object:
        app.config.from_object(config_object)
    else:
        app_env = os.getenv("APP_ENV", "development").lower()
        if app_env == "production":
            from config import ProdConfig as Cfg
        elif app_env == "test":
            from config import TestConfig as Cfg
        else:
            from config import DevConfig as Cfg
        app.config.from_object(Cfg)

    csrf.init_app(app)
    init_services(app)

    from app.blueprints.dashboard import bp as dashboard_bp
    from app.blueprints.transactions import bp as transactions_bp
    from app.blueprints.budgets import bp as budgets_bp
    from app.blueprints.goals import bp as goals_bp
    from app.blueprints.importqr import bp as importqr_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.export import bp as export_bp
    from app.blueprints.receipts import bp as receipts_bp
    from app.blueprints.incomes import bp as incomes_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(importqr_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(incomes_bp)

    swaggerui_blueprint = get_swaggerui_blueprint(
        app.config["SWAGGER_URL"],
        app.config["API_URL"],
        config={"app_name": "Receipts API"}
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=app.config["SWAGGER_URL"])

    return app

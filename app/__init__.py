from flask import Flask
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
import os

csrf = CSRFProtect()

def create_app(config_object=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
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

    from app.blueprints.dashboard import bp as dashboard_bp
    from app.blueprints.transactions import bp as transactions_bp
    from app.blueprints.budgets import bp as budgets_bp
    from app.blueprints.goals import bp as goals_bp
    from app.blueprints.importqr import bp as importqr_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.export import bp as export_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(importqr_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(export_bp)

    return app

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()


def create_app():
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/'
    )

    # Sqlite used only for testing purposes. For production PostgreSQL or MySQL will be used.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    db.init_app(app)

    from . import routes
    app.register_blueprint(routes.bp)

    migrate = Migrate(app, db)

    return app

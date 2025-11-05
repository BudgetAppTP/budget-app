"""
Smoke tests for the Budget Tracker application.

These tests verify that the application can start and basic infrastructure works.
"""
import os
import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app()

    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    return app.test_client()


def test_app_creates_successfully(app):
    """Test that the application factory creates an app instance."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_database_connection(app):
    """Test that database connection is established."""
    with app.app_context():
        assert db.engine is not None


def test_database_tables_created(app):
    """Test that database tables are created successfully."""
    with app.app_context():
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        assert len(tables) > 0


def test_app_context_works(app):
    """Test that Flask application context functions correctly."""
    with app.app_context():
        assert app.config is not None
        assert app.extensions is not None


def test_app_env_is_test():
    """Test that APP_ENV environment variable is set to 'test'."""
    app_env = os.getenv("APP_ENV", "").lower()
    assert app_env == "test", (
        f"APP_ENV must be set to 'test' for tests to run safely. "
        f"Current value: '{app_env}'. Check pytest.ini configuration."
    )

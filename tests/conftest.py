from __future__ import annotations

from http.cookies import SimpleCookie

import pytest

from app import create_app
from app.extensions import db
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def cookie_value(response, name: str) -> str:
    cookie = SimpleCookie()
    for header in response.headers.getlist("Set-Cookie"):
        cookie.load(header)
    return cookie[name].value


def register_user(client, email="user@test.local", password="pass"):
    response = client.post("/api/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response


def login_user(client, email="user@test.local", password="pass"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response


@pytest.fixture
def auth_client_factory(app):
    def factory(email: str, password: str = "pass"):
        test_client = app.test_client()
        register_user(test_client, email=email, password=password)
        login_user(test_client, email=email, password=password)
        return test_client

    return factory

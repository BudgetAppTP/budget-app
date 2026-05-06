from app.extensions import db
from app.models import User


def test_registration_normalizes_email_hashes_password_and_blocks_duplicate(client, app):
    registered = client.post(
        "/api/auth/register",
        json={"email": "CaseSensitive@Test.Local", "password": "plain-password"},
    )
    assert registered.status_code == 201

    with app.app_context():
        user = db.session.execute(db.select(User).filter_by(email="casesensitive@test.local")).scalar_one()
        assert user.password_hash != "plain-password"
        assert "plain-password" not in user.password_hash

    duplicate = client.post(
        "/api/auth/register",
        json={"email": "casesensitive@test.local", "password": "another-password"},
    )

    assert duplicate.status_code == 409
    assert duplicate.get_json()["error"]["code"] == "exists"


def test_protected_endpoints_require_authentication(client):
    protected_paths = [
        "/api/incomes",
        "/api/categories",
        "/api/tags/income",
        "/api/monthly-budget?month=2025-10",
        "/api/dashboard/summary?year=2025&month=10",
    ]

    for path in protected_paths:
        response = client.get(path)
        assert response.status_code == 401, path
        assert response.get_json()["error"]["code"] == "unauthenticated"

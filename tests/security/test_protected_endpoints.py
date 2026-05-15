import pytest


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/funds"),
        ("post", "/api/funds"),
        ("put", "/api/funds/00000000-0000-0000-0000-000000000001"),
        ("get", "/api/funds/00000000-0000-0000-0000-000000000001/goals"),
        ("post", "/api/funds/00000000-0000-0000-0000-000000000001/goals"),
        ("put", "/api/goals/00000000-0000-0000-0000-000000000001"),
        ("patch", "/api/goals/00000000-0000-0000-0000-000000000001/status"),
        ("get", "/api/dashboard/summary"),
        ("get", "/api/incomes"),
        ("post", "/api/incomes"),
        ("get", "/api/receipts"),
        ("post", "/api/receipts"),
        ("get", "/api/receipts/ekasa-items"),
        ("post", "/api/receipts/import-ekasa"),
        ("get", "/api/tags/income"),
        ("get", "/api/tags/expense"),
        ("post", "/api/tags"),
        ("get", "/api/categories"),
        ("post", "/api/categories"),
        ("get", "/api/categories/monthly-limit"),
        ("get", "/api/monthly-budget"),
        ("get", "/api/analytics/donut"),
    ],
)
def test_every_private_api_endpoint_requires_authentication(client, method, path):
    response = getattr(client, method)(path, json={})

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthenticated"

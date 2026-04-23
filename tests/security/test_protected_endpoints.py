import pytest


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/transactions"),
        ("post", "/api/transactions"),
        ("get", "/api/budgets"),
        ("put", "/api/budgets/2025-10"),
        ("get", "/api/goals"),
        ("post", "/api/goals"),
        ("put", "/api/goals/example-id"),
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

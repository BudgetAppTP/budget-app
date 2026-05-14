# Test Suite

This folder contains the backend test suite for the Budget App. The goal is to
cover the security-sensitive API behavior, core business rules, and basic
application health checks with tests that can run locally and in CI.

## How to Run

Run the full suite from the project root:

```bash
make test
```

Equivalent direct pytest command:

```bash
python -m pytest
```

The CI pipeline also runs pytest with `APP_ENV=test`.

## Structure

```text
tests/
  conftest.py
  README.md
  test_auth_sessions.py
  test_smoke.py
  integration/
  security/
  unit/
```

### `conftest.py`

Shared pytest setup.

It provides:

- Flask app creation with `TestConfig`.
- Test client fixtures.
- Auth helper functions.
- `auth_client_factory`, used to create independent logged-in clients for
  cross-user authorization tests.

### `security/`

Security regression tests for authentication and authorization.

Covered areas:

- Registration rejects missing required fields.
- Login rejects incomplete or invalid credentials.
- Login normalizes email case.
- Logout without a token is safe and clears the cookie.
- Invalid bearer tokens are rejected.
- Private API endpoints require authentication.
- User-owned resources do not trust caller-supplied `user_id`.
- Cross-user access attempts return `401` or `404`.

### `integration/`

API-level tests that exercise Flask routes, database persistence, request
parsing, and service behavior together.

Covered areas:

- Income create/update/delete validation.
- Income month filtering and sorting.
- Dashboard and monthly budget totals.
- Budget seeding and update persistence.
- Category validation and ownership.
- Tag validation, duplicate handling, type filtering, and counters.
- Receipt and receipt-item validation.
- Receipt and receipt-item cross-user authorization.

### `unit/`

Fast tests for isolated business logic.

These tests should not need Flask, HTTP clients, or the database unless the
tested behavior specifically belongs to a model/repository boundary.

Current examples:

- Decimal parsing and rounding.
- Invalid decimal handling.
- Non-negative validation.
- Month format validation.

### `test_auth_sessions.py`

Session lifecycle integration tests.

Covered areas:

- Login creates an HTTP-only cookie.
- `/api/auth/me` resolves cookie and bearer-token sessions.
- Logout revokes only the current session.
- Expired tokens are rejected and cleaned up.
- Invalid login does not create a token.
- Income creation ignores malicious payload `user_id`.

### `test_smoke.py`

Broad smoke tests for application startup and representative endpoints.

These tests check that:

- The app factory works.
- The database is initialized.
- Core public/private endpoints respond.
- The seeder remains compatible with the current schema.

## Naming Conventions

- Test files use `test_<area>.py`.
- Test functions use `test_<expected_behavior>`.
- Helpers are kept local to a file unless they are useful across suites.
- Shared helpers belong in `conftest.py`.

## Test Types

Pytest markers are declared in `pytest.ini`:

- `unit`: pure or near-pure logic tests.
- `integration`: Flask/database/API integration tests.
- `security`: authentication and authorization regression tests.

Markers are available for selective runs, for example:

```bash
python -m pytest -m security
```

## Critical Coverage Areas

Keep coverage focused on these areas:

- Authentication: registration, login, logout, token expiry, cookie flags,
  duplicate accounts, password hashing.
- Authorization: every private API requires auth; user-owned resources ignore
  payload/query `user_id`; cross-user reads, updates, and deletes fail safely.
- API contract: status codes, validation errors, and the JSON envelope shape.
- Core business logic: dates, months, money parsing, totals, budgets, tags,
  categories, receipts, and receipt items.
- CI readiness: the suite must run without external services or network access.

## Known Gaps

- Goals are currently global in-memory records with no user ownership field.
  The suite contains an `xfail` test documenting the expected future behavior.
- Financial target API endpoints do not currently exist. The suite contains a
  skipped placeholder test for future endpoint-level authorization coverage.

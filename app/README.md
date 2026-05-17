# Backend README

This folder contains the Flask backend for Budget Tracker. It exposes a JSON-only API, serves Swagger UI, manages persistence and business rules, and supports local development, Docker-based review, and production deployment.

## Overview

- App entrypoint: [app/run.py](./run.py)
- App factory: [app/__init__.py](./__init__.py)
- Configuration: [app/config.py](./config.py)
- Swagger UI: `/api/docs`
- OpenAPI document served from: `/static/swagger.json`

The backend does not render server-side HTML for the running application. The user-facing interface lives in the React client.

## Environment Modes

The backend selects configuration from `APP_ENV`:

| `APP_ENV` value | Intended use | Database default |
| --- | --- | --- |
| `development` | Local backend development | SQLite in `instance/dev.db` |
| `docker-local` | Local Docker Compose stack | PostgreSQL container |
| `production` | Production runtime | PostgreSQL |
| `test` | Automated tests | in-memory SQLite |

`DEBUG=true` is enabled by default in local development. In production, set `APP_ENV=production` and keep `DEBUG=false` unless you are debugging a controlled environment.

## API Behavior

### Response Envelope

API routes live under `/api/*` and use a unified JSON envelope:

```json
{
  "data": {},
  "error": null
}
```

On errors, `data` becomes `null` and `error` contains a code/message object.

### Authentication

- Public routes include `/api/auth/*` and `/api/health`
- Most other API routes require authentication
- The backend accepts either:
  - the `auth_token` cookie
  - an `Authorization: Bearer <token>` header

Swagger UI is the canonical reference for current endpoint shapes and grouped capabilities. Use the live docs at `/api/docs` instead of maintaining a second hand-written endpoint inventory.

## Configuration

The main sample environment file is [../.env.example](../.env.example).

### Common Required Settings

These should be reviewed for any real deployment:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Selects the active backend configuration |
| `SECRET_KEY` | Flask secret used for sessions and security-sensitive behavior |
| `DATABASE_URL` | Database connection string for Docker/production |
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | PostgreSQL database name |

### Common Optional Settings

| Variable | Purpose |
| --- | --- |
| `DEBUG` | Enables debug behavior in local environments |
| `HOST` | Host binding for `python -m app.run` |
| `PORT` | Backend port, default `5000` |
| `DEFAULT_CURRENCY` | Default currency code |
| `IMPORT_XLSX_PATH` | Spreadsheet import path used by the backend |
| `MAX_SAVINGS_FUNDS` | Limit for configured savings funds |

### Frontend/Proxy-Related Settings

These are kept in the root `.env` because Docker Compose shares them across services:

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | API base used by the frontend build |
| `VITE_PROXY_TARGET` | Dev proxy target used by the frontend |
| `FRONTEND_PORT` | Host port exposed by the reverse proxy |
| `BASIC_AUTH_USER` | HTTP Basic Auth username for Docker-exposed review environments |
| `BASIC_AUTH_PASSWORD` | HTTP Basic Auth password for Docker-exposed review environments |

## Database Behavior

- Local `development` mode uses SQLite and stores the file at `instance/dev.db`
- `docker-local` and `production` use PostgreSQL
- `test` uses in-memory SQLite for fast isolated runs

The project already includes Flask-Migrate and Alembic, but current startup behavior still calls `create_all()` when `DEBUG` or `TESTING` is enabled. That means local development and tests can bootstrap tables automatically without running migrations first.

## Local Backend Run

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
cp .env.example .env
python -m app.run
```

The backend then listens on `http://127.0.0.1:5000` by default.

If you prefer the project shortcuts, you can also run:

```bash
make venv
make run
```

These shortcuts work best in a POSIX-style shell such as Linux, macOS, WSL, or Git Bash.

## Testing

Run the backend test suite from the project root:

```bash
make test
```

For test-suite structure, markers, and coverage notes, see [../tests/README.md](../tests/README.md).

## Auth Integrations

### Email Verification / SMTP

Registration uses a six-digit verification code flow.

- In `development` and `test`, accounts are effectively auto-verified to keep local work simple
- In production, configure SMTP and disable debug/test behavior so users must verify their email before logging in

Supported SMTP variables:

- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`

If SMTP is not fully configured, the backend logs the verification code to the server output instead of sending email. That is helpful for local development but should not be relied on in production.

### Google OAuth

Google sign-in is enabled when both sides are configured:

- Backend: `GOOGLE_CLIENT_ID` in [../.env.example](../.env.example)
- Frontend: `VITE_GOOGLE_CLIENT_ID` in [../client/.env.example](../client/.env.example)

These values must refer to the same Google OAuth client ID. The frontend obtains the ID token, and the backend validates it.

## Deployment

Production deployment is split between infrastructure and application services.

### Compose Layout

- [../docker-compose-prod-infra.yml](../docker-compose-prod-infra.yml)
  - PostgreSQL
  - external nginx
  - shared production Docker network
- [../docker-compose-prod-services.yml](../docker-compose-prod-services.yml)
  - backend
  - frontend
  - attaches to the existing production network

Start infrastructure first, then services. That order matters locally and mirrors the intended deployment flow:

```bash
make docker-prod-infra-up
make docker-prod-services-up
```

To stop them in the reverse order:

```bash
make docker-prod-services-down
make docker-prod-infra-down
```

### GitHub Actions Workflows

- [../.github/workflows/deploy-prod-infra.yml](../.github/workflows/deploy-prod-infra.yml)
  - manual deployment of production infrastructure
  - can deploy PostgreSQL, nginx, or both
- [../.github/workflows/deploy-prod-services.yml](../.github/workflows/deploy-prod-services.yml)
  - builds backend and frontend images
  - deploys application services
- [../.github/workflows/run-tests.yml](../.github/workflows/run-tests.yml)
  - runs lint checks and `pytest`

### Required Deployment Secrets / Variables

Review these before using the production workflows:

- `DEPLOY_SSH_PRIVATE_KEY`
- `DEPLOY_SSH_HOST`
- `DEPLOY_SSH_USER`
- `DEPLOY_SSH_PORT`
- `REMOTE_APP_DIR`
- `GHCR_TOKEN`
- `GHCR_USERNAME`
- `PROD_DOCKER_NETWORK`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `SECRET_KEY`
- `BASIC_AUTH_USER`
- `BASIC_AUTH_PASSWORD`

Production image references are also required when using the production Compose files locally:

- `BACKEND_IMAGE`
- `FRONTEND_IMAGE`
- `EXTERNAL_NGINX_IMAGE`

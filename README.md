# Budget Tracker App

Personal finance tracker for budgeting, expense tracking, and goal setting.

## Overview

This repository now consists of two parts:

* **Backend:** Flask **JSON-only API** under `/api/*`
  Unified response shape:

  ```json
  { "data": ..., "error": { "code": "...", "message": "..." } | null }
  ```
* **Frontend:** React client (Vite) in `client/`

Server-side rendering (Jinja) is not used by the running app.

```
budget-app/
  app/
    __init__.py
    Dockerfile
    requirements.txt
    api/
      account.py
      allocations.py
      analytics.py
      auth.py
      categories.py
      dashboard.py
      export.py
      goals.py
      importqr.py
      incomes.py
      monthly_budget.py
      receipt_items.py
      receipts.py
      savings_funds.py
      tags.py
      users.py
    core/
    models/
    services/
    validators/
    run.py
    config.py
client/
  index.html
  Dockerfile.dev
  Dockerfile.prod
  package.json
  tsconfig.json
  vite.config.js
  src/
    main.jsx
    App.jsx
    api/http.ts
    api/endpoints.ts
    components/
      Layout.jsx
      Navbar.jsx
    pages/
      Dashboard.jsx
      Budgets.jsx
      Ekasa.jsx
      Expenses.jsx
      Incomes.jsx
      Login.jsx
      Savings.jsx
      Signin.jsx
tests/
  pytest.ini
  test_smoke.py
.env.example
docker-compose.yaml
docker-compose-prod-infra.yml
docker-compose-prod-services.yml
```

---

## Run the App

### Using the Makefile (Simple)

This project includes a `Makefile` to simplify common tasks such as setting up a virtual environment, running the project, running tests, and cleaning up temporary files.

* Install `make` on Linux (Ubuntu):

```bash
sudo apt update
sudo apt install build-essential
```

* Install `make` on Windows: [https://stackoverflow.com/a/32127632](https://stackoverflow.com/a/32127632)

#### Available Targets

| Target  | Description                                                                    |
| ------- | ------------------------------------------------------------------------------ |
| `help`  | Show the help message listing all targets.                                     |
| `venv`  | Create a virtual environment and install dependencies from `app/requirements.txt`. |
| `run`   | Run the backend using the virtual environment Python interpreter.              |
| `test`  | Run tests using `pytest` inside the virtual environment.                       |
| `clean` | Remove the virtual environment and all `__pycache__` directories.              |
| `docker-build` | Build Docker images for development (`docker-compose.yaml`).           |
| `docker-up` | Start development Docker stack (with build).                              |
| `docker-down` | Stop development Docker stack.                                          |
| `docker-logs` | Show logs for development Docker stack.                                 |
| `docker-prod-build` | Pull production images (infra + services).                        |
| `docker-prod-up` | Start production stack (infra then services).                       |
| `docker-prod-down` | Stop production stack (services then infra).                      |
| `docker-prod-infra-up` | Start production infra only (`db` + external nginx).         |
| `docker-prod-services-up` | Start production services only (`backend` + `frontend`).  |
| `docker-prod-infra-logs` | Show logs for production infra.                              |
| `docker-prod-services-logs` | Show logs for production services.                        |

### Basic Usage

1. Create a virtual environment and install dependencies:

```bash
make venv
```

2. Run the backend:

```bash
make run
```

> **Windows note:** The Makefile works best in a POSIX-compatible shell (Git Bash or WSL). In `cmd.exe` some targets may not work correctly.

---

## Docker Run (Dev/Prod)

### Development stack

```bash
make docker-up
# or: docker compose -f docker-compose.yaml up --build
```

The local Docker stack runs `postgres`, `backend`, `frontend`, and `external-nginx` together.
It was added to simulate the production topology locally while still building images from the
working tree. The backend connects to PostgreSQL through the Compose network, and nginx exposes
the app through a single entrypoint.

Frontend runs on `http://localhost:5173` by default (`FRONTEND_PORT` can override host port).
Access is protected with HTTP Basic Auth via `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD`.

### Production stack

```bash
make docker-prod-up
# or split deploy:
# docker compose -f docker-compose-prod-infra.yml up -d --no-build
# docker compose -f docker-compose-prod-services.yml up -d --no-build
```

Before starting production compose locally, set image refs in `.env`:
`BACKEND_IMAGE`, `FRONTEND_IMAGE`, `EXTERNAL_NGINX_IMAGE`.

Frontend (nginx) runs on `http://localhost:80` by default (`FRONTEND_PORT` can override host port; for local prod set `FRONTEND_PORT=80` if needed).
Access is protected with HTTP Basic Auth via `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD`.

The production Compose setup is intentionally split:

* `docker-compose-prod-infra.yml`: long-lived infrastructure (`db` and `external-nginx`) and the shared `${PROD_DOCKER_NETWORK}` network.
* `docker-compose-prod-services.yml`: application services (`backend` and `frontend`) that attach to the existing production network.

For local production simulation, start infra before services. In GitHub deploys, the services
script can create the missing network as a fallback, but the intended flow is still infra first.

### Stop stacks

```bash
make docker-down
make docker-prod-down
```

---

## GitHub Deploy Workflows

Production deploys are split so stable infrastructure can be changed separately from the
application code:

* `.github/workflows/deploy-prod-infra.yml` is manual (`workflow_dispatch`) and deploys
  `postgres`, `nginx`, or both. The nginx image is built and pushed only when the selected
  target includes nginx.
* `.github/workflows/deploy-prod-services.yml` runs automatically on pushes to `main` and
  `master`, and can also be run manually. It builds backend/frontend images, pushes them to
  GHCR, then deploys only the services that changed.

Both workflows deploy `github.ref_name`: for manual runs this is the ref selected in
**Use workflow from**, and for push runs this is the pushed branch. The deploy scripts sync the
remote checkout to that ref, log in to GHCR, pull the target image(s), and run Docker Compose over
SSH. A custom git remote name can be supplied with `deploy_git_remote` (default `origin`).

Deploy scripts keep lightweight hashes in `.deploy_state` on the server. A container is recreated
when relevant files changed, the container is missing, or the pulled image differs from the
running image.

Required GitHub Secrets:

* `DEPLOY_SSH_PRIVATE_KEY`
* `GHCR_TOKEN`
* `POSTGRES_USER`
* `POSTGRES_PASSWORD`
* `POSTGRES_DB`
* `BASIC_AUTH_USER`
* `BASIC_AUTH_PASSWORD`
* `SECRET_KEY`

Store sensitive runtime values as GitHub repository or environment **Secrets**. Non-sensitive
connection and deploy settings can be configured either as Secrets or as Variables; the workflows
read them as `secrets.* || vars.*`:

* `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_PORT`, `REMOTE_APP_DIR`
* `PROD_DOCKER_NETWORK`
* `DEPLOY_GIT_REMOTE`
* `GHCR_USERNAME`

`GHCR_TOKEN` is used both for authenticated git fetches on the deploy host and for pulling images
from GHCR. Remote host requirement: deploy user must have access to Docker daemon (either docker
group membership or passwordless `sudo` for docker commands).

---

## Manual Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (Powershell):
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r app/requirements.txt
```

3. Configure environment (optional):

```bash
cp .env.example .env
```

4. Run the backend (Flask API):

```bash
python -m app.run
# API base: http://127.0.0.1:5000/api
```

---

## Frontend (React, Vite + TypeScript)

1. Install dependencies:

```bash
cd client
npm i
```

2. Start the dev server:

```bash
npm run dev
# Opens http://localhost:5173
```

The dev proxy in `vite.config.js` forwards `/api/*` to `VITE_PROXY_TARGET` (default: `http://localhost:5000`). In Docker development compose, `VITE_PROXY_TARGET` is set to `http://backend:5000`.

### Parallel Run

* Terminal A:

```bash
python -m app.run
```

* Terminal B:

```bash
cd client
npm i
npm run dev
```

---

## API Endpoints

* **Auth**

  * `POST /api/auth/login`
  * `POST /api/auth/register`
  * `POST /api/auth/verify`
  * `GET /api/auth/me`
  * `POST /api/auth/logout`
  * `POST /api/auth/google`

* **Accounts, budgets, and analytics**

  * `GET /api/account`
  * `PATCH /api/account`
  * `GET /api/monthly-budget?year=YYYY&month=M`
  * `GET /api/dashboard/summary`
  * `GET /api/analytics/donut`

* **Incomes**

  * `GET /api/incomes`
  * `POST /api/incomes`
  * `GET /api/incomes/:id`
  * `PUT /api/incomes/:id`
  * `DELETE /api/incomes/:id`
  * `GET /api/incomes/tags`

* **Receipts and receipt items**

  * `GET /api/receipts`
  * `POST /api/receipts`
  * `GET /api/receipts/:id`
  * `PUT /api/receipts/:id`
  * `DELETE /api/receipts/:id`
  * `POST /api/receipts/import-ekasa`
  * `GET /api/receipts/ekasa-items`
  * `GET|POST /api/receipts/:receipt_id/items`
  * `PUT|DELETE /api/receipts/:receipt_id/items/:item_id`

* **Categories and tags**

  * `GET|POST /api/categories`
  * `GET /api/categories/monthly-limit`
  * `PUT|DELETE /api/categories/:id`
  * `GET /api/tags/income`
  * `GET /api/tags/expense`
  * `POST /api/tags`
  * `PUT|DELETE /api/tags/:id`

* **Savings funds, goals, and allocations**

  * `GET /api/savings/summary`
  * `GET|POST /api/funds`
  * `GET|PUT|PATCH|DELETE /api/funds/:id`
  * `PATCH /api/funds/:id/status`
  * `PATCH /api/funds/:id/balance`
  * `GET|POST /api/funds/:fund_id/goals`
  * `PUT|PATCH|DELETE /api/goals/:id`
  * `PATCH /api/goals/:id/status`
  * `PATCH /api/goals/:id/amount`
  * `GET|POST /api/savings-funds/:fund_id/allocations`
  * `DELETE /api/savings-funds/:fund_id/allocations/:allocation_id`

* **Import QR**

  * `POST /api/import-qr/extract-id`

* **Export**

  * `GET /api/export/csv?year=YYYY&month=M`  *(file download)*
  * `GET /api/export/pdf?year=YYYY&month=M`  *(file download)*

* **Users and health**

  * `GET /api/users`
  * `POST /api/users`
  * `GET /api/health`

All endpoints return `application/json` except file downloads under `/api/export/*`.
All API routes except auth routes and `/api/health` require a valid session token, accepted either
from the `auth_token` cookie or a `Bearer` token.

> API docs UI (Swagger) can be enabled if desired. If configured, it is typically exposed under something like `/api/docs`.

---

## Project Structure (Details)

* `app/__init__.py`: Flask app factory, CORS, error handlers, and API blueprint registration.
* `app/api/*`: JSON controllers (auth, account, analytics, categories, goals, import QR, export, dashboard, incomes, receipts, receipt items, savings funds, tags, users).
* `app/core/*`: domain entities and DTOs.
* `app/services/*`: business logic, repositories, and stubs.
* `client/*`: React (Vite + TS) scaffold, router, API client, and basic pages.
* `tests/test_smoke.py`: smoke tests against `/api/*`.

---

## Testing

Run the test suite:

```bash
make test
# or: python -m pytest -c tests/pytest.ini
```

Smoke tests assert:

* Health: `/api/health`
* Core lists and shapes: authenticated finance, savings, dashboard, and export endpoints
* Auth flow: register → login → logout
* Import QR extraction
* Export CSV/PDF (file responses)

---

## Database

This application uses **PostgreSQL** in production and **SQLite** in development and testing environments.

> [!NOTE]
> In development mode, the SQLite database file is located at: \
> ```<project_root>/instance/dev.db``` \
> *For more details, see `app/config.py`.*


### Database Setup (Current Development Stage)

`Flask-Migrate` and `Alembic` are configured in the project, but current startup flow still uses automatic table creation in debug/testing mode (`create_all`).


### How to Create or Recreate the Database (SQLite)

1. Remove the existing database file:
``` bash
rm instance/dev.db
```
2. Restart the application.

The app will automatically recreate all database tables defined in models.
After the first startup, you’ll have a new, clean database ready to use.


### Generate an Entity Relationship Diagram with ERAlchemy
You can easily visualize the project's database schema using **ERAlchemy** directly from SQLite `.db` file
#### Install ERAlchemy:

```bash
pip install eralchemy
eralchemy -i sqlite:///instance/dev.db -o db_schema.png
```

* `-i` input database URI
* `-o` output file (`.png`, `.pdf`, or `.svg`)

---

## Dependencies (Trimmed)

The backend no longer uses Jinja/WTForms/Excel stack. Core dependencies include:

* Flask, Flask-CORS
* SQLAlchemy, Flask-SQLAlchemy, Alembic, Flask-Migrate
* python-dotenv
* reportlab (PDF export)
* pytest
* (optional) flask_swagger_ui

Exact versions are pinned in `app/requirements.txt`.

---

## Email Verification & SMTP Configuration

The authentication system sends a six‑digit verification code to new users during registration. In development and test modes the backend auto‑verifies accounts (controlled by the `DEBUG`/`TESTING` flags) to simplify local work. In production you should disable these flags and configure SMTP so that users receive a code via email and must verify their address before logging in.

To enable email delivery:

1. Copy `.env.example` to `.env` if you haven't already: this file now includes blank `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER` and `SMTP_PASSWORD` variables.
2. Fill these variables with your SMTP provider settings. For example, Gmail would use:

   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_address@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

3. Set `APP_ENV=production` and ensure `DEBUG`/`TESTING` are not set so users must verify their email before they can log in.

If the SMTP configuration is incomplete, the server logs the verification code instead of sending it. This allows you to sign up locally without a running mail server. Check the console output where the backend is running to retrieve the code.

---

## Development Notes

* Controllers in `app/api/*` must return the unified JSON shape `{ data, error }`.
* Keep presentation logic out of the backend. All UI belongs to the React client.
* Prefer adding new endpoints under `/api/*` and evolve contracts versioned if needed (e.g., `/api/v1/*`).

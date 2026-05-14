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
      auth.py
      transactions.py
      budgets.py
      goals.py
      importqr.py
      export.py
      dashboard.py
      incomes.py
      receipts.py
      receipt_items.py
      users.py
    core/
    services/
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
      Expenses.jsx
      Incomes.jsx
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
`docker-compose-prod-services.yml` expects network `${PROD_DOCKER_NETWORK}` to exist (it is created by `docker-compose-prod-infra.yml`).

### Stop stacks

```bash
make docker-down
make docker-prod-down
```

---

## GitHub Deploy Workflows

Production deploy is split into two workflows:

* `.github/workflows/deploy-prod-infra.yml` (manual): deploys `postgres`, `nginx`, or both.
* `.github/workflows/deploy-prod-services.yml` (push to `main` + manual): builds backend/frontend images and deploys services.

Both workflows deploy the ref selected in **Use workflow from** (`github.ref_name`) and support custom git remote name via `deploy_git_remote` (default `origin`).

Required GitHub Secrets:

* `DEPLOY_SSH_PRIVATE_KEY`
* `GHCR_TOKEN`
* `POSTGRES_USER`
* `POSTGRES_PASSWORD`
* `POSTGRES_DB`
* `BASIC_AUTH_USER`
* `BASIC_AUTH_PASSWORD`
* `SECRET_KEY`

Connection and deploy settings can be configured either via Secrets or via Variables (workflow uses `secrets.* || vars.*`):

* `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_PORT`, `REMOTE_APP_DIR`
* `PROD_DOCKER_NETWORK`
* `DEPLOY_GIT_REMOTE`
* `GHCR_USERNAME`

Remote host requirement: deploy user must have access to Docker daemon (either docker group membership or passwordless `sudo` for docker commands).

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

## API Endpoints (Minimum)

* **Auth**

  * `POST /api/auth/login`
  * `POST /api/auth/register`
  * `POST /api/auth/logout`

* **Transactions**

  * `GET /api/transactions` (filters: `month`, `kind`, `category`, `search`)
  * `POST /api/transactions`

* **Budgets**

  * `GET /api/budgets?month=YYYY-MM`
  * `PUT /api/budgets/:month` (bulk-upsert sections)

* **Goals**

  * `GET /api/goals`
  * `POST /api/goals`
  * `PUT /api/goals/:id`

* **Import QR**

  * `POST /api/import-qr/preview`
  * `POST /api/import-qr/confirm`

* **Export**

  * `GET /api/export/csv?month=YYYY-MM`  *(file download)*
  * `GET /api/export/pdf?month=YYYY-MM`  *(file download)*

* **Dashboard**

  * `GET /api/dashboard?month=YYYY-MM`

All endpoints return `application/json` except file downloads under `/api/export/*`.

> API docs UI (Swagger) can be enabled if desired. If configured, it is typically exposed under something like `/api/docs`.

---

## Project Structure (Details)

* `app/__init__.py`: Flask app factory, CORS, error handlers, and API blueprint registration.
* `app/api/*`: JSON controllers (auth, transactions, budgets, goals, import-qr, export, dashboard, incomes, receipts, receipt_items, users).
* `app/core/*`: domain entities and DTOs.
* `app/services/*`: business logic, repositories, and stubs.
* `client/*`: React (Vite + TS) scaffold, router, API client, and basic pages.
* `tests/test_smoke.py`: smoke tests against `/api/*`.

---

## Testing

Run the test suite:

```bash
pytest -q
```

Smoke tests assert:

* Health: `/api/health`
* Core lists and shapes: `/api/transactions`, `/api/budgets`, `/api/goals`, `/api/dashboard`
* Auth flow: register → login → logout
* Import QR preview
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

## Development Notes

* Controllers in `app/api/*` must return the unified JSON shape `{ data, error }`.
* Keep presentation logic out of the backend. All UI belongs to the React client.
* Prefer adding new endpoints under `/api/*` and evolve contracts versioned if needed (e.g., `/api/v1/*`).

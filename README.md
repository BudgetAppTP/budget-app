# Budget Tracker App

Personal finance tracker for budgeting, expense tracking, and goal setting.

## Overview

This repository now consists of two parts:

* **Backend:** Flask **JSON-only API** under `/api/*`
  Unified response shape:

  ```json
  { "data": ..., "error": { "code": "...", "message": "..." } | null }
  ```
* **Frontend:** React client (Vite + TypeScript) in `client/`

Server-side rendering (Jinja) was removed from the running app. All legacy templates and static assets were archived for the designer to port into React.

```
budget_app/
  app/
    __init__.py
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
  legacy_templates/      # archived Jinja templates (for designer)
  static_legacy/         # archived legacy static assets
  run.py
  config.py
client/
  index.html
  package.json
  tsconfig.json
  vite.config.ts
  src/
    main.tsx
    App.tsx
    api/http.ts
    api/endpoints.ts
    components/
      Layout.tsx
      Navbar.tsx
    pages/
      Dashboard.tsx
      Transactions.tsx
      Budgets.tsx
      Goals.tsx
      ImportQR.tsx
tests/
  test_smoke.py
.env.example
requirements.txt
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
| `venv`  | Create a virtual environment and install dependencies from `requirements.txt`. |
| `run`   | Run the backend using the virtual environment Python interpreter.              |
| `test`  | Run tests using `pytest` inside the virtual environment.                       |
| `clean` | Remove the virtual environment and all `__pycache__` directories.              |

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
pip install -r requirements.txt
```

3. Configure environment (optional):

```bash
cp .env.example .env
```

4. Run the backend (Flask API):

```bash
python budget_app/run.py
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

The dev proxy in `vite.config.ts` forwards `/api/*` to `http://localhost:5000`, so the client can call the API without extra CORS configuration during development. The backend additionally allows CORS for `http://localhost:5173` on `/api/*`.

### Parallel Run

* Terminal A:

```bash
python budget_app/run.py
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

* `budget_app/app/__init__.py`: Flask app factory, CORS, error handlers, and API blueprint registration. Flask’s `template_folder` and `static_folder` are disabled to enforce API-only behavior.
* `budget_app/app/api/*`: JSON controllers (auth, transactions, budgets, goals, import-qr, export, dashboard, incomes, receipts, receipt_items, users).
* `budget_app/app/core/*`: domain entities and DTOs.
* `budget_app/app/services/*`: business logic, repositories, and stubs.
* `budget_app/legacy_templates/` and `budget_app/static_legacy/`: archived legacy Jinja pages and assets for the designer to port into React. Not used by the running backend.
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
> *For more details, see `config.py`.*


### Database Setup (Current Development Stage)

At this stage of the project, **Flask-Migrate** and **Alembic** migrations are disabled.
Because the database schema is still evolving rapidly, it’s simpler and faster to recreate the database from the models whenever the schema changes.

Once the data model stabilizes, migrations will be re-enabled to manage schema updates safely in production environments.


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

Exact versions are pinned in `requirements.txt`.

---

## Development Notes

* Controllers in `app/api/*` must return the unified JSON shape `{ data, error }`.
* Keep presentation logic out of the backend. All UI belongs to the React client.
* Prefer adding new endpoints under `/api/*` and evolve contracts versioned if needed (e.g., `/api/v1/*`).

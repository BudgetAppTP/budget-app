# budget-app
Personal finance tracker for budgeting, expense tracking, and goal setting.

## Quick Start (EN)

### Run
```bash
cd budget_app
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env
python run.py
````

### What is what

* `run.py` — app entry point (dev server).
* `config.py` — app configuration (Dev/Test/Prod), reads `.env`.
* `app/` — main application package.

  * `__init__.py` — Flask app factory, blueprint wiring, services init.
  * `blueprints/` — feature modules (routes + forms + templates):

    * `dashboard/` — `/` overview, charts data.
    * `transactions/` — list, filters, create income/expense.
    * `budgets/` — monthly budgets overview & edit.
    * `goals/` — goals list & edit.
    * `importqr/` — QR/eKasa JSON import (preview + confirm).
    * `auth/` — login/register/logout (stub, in-memory).
    * `export/` — CSV (real) and PDF (placeholder) export.
  * `core/` — domain layer:

    * `domain.py` — entities (Money, Transaction, MonthlyBudget, Goal, User).
    * `dto.py` — filter/aggregate DTOs.
    * `validators.py` — parsing/validation helpers.
  * `services/` — in-memory repos + stubs:

    * `repositories.py` — interfaces.
    * `repository_inmemory.py` — data store with seeds and optional XLSX import.
    * `qr_parser_stub.py`, `ekasa_client_stub.py` — import/validation stubs.
    * `export_stub.py` — CSV export (real), PDF placeholder.
    * `auth_stub.py` — sha256 “hashing” + fake session helpers.
  * `templates/` — Jinja templates (UI text in Slovak):

    * `base.html`, `_navbar.html`, `_flash.html`
    * pages under `dashboard/`, `transactions/`, `budgets/`, `goals/`, `importqr/`, `auth/`
  * `static/` — CSS/JS assets (`css/app.css`, `js/charts.js`)
* `tests/` — smoke tests for key routes.
* `.env.example` — sample environment variables (copy to `.env`).
* `requirements.txt` — Python dependencies.

### API Documentation
 The REST API endpoints are documented and can be explored via Swagger UI.

After starting the app, open this URL in your browser: 

http://127.0.0.1:5000/api/docs 

It provides interactive documentation for REST endpoints (incomes, receipts).

### Notes

* Optional import from Excel: set `IMPORT_XLSX_PATH` in `.env` (ignored if file not found).


## Database
### Overview

This application uses **PostgreSQL** in production and **SQLite** in development and testing environments.

> [!NOTE]
> In development mode, the SQLite database file is located at: \
> ```<project_root>/instance/dev.db``` \
> *For more details, see `config.py`.*

### Generate an Entity Relationship Diagram with ERAlchemy
You can easily visualize the project's database schema using **ERAlchemy** directly from SQLite `.db` file
#### Install ERAlchemy:

``` bash
pip install eralchemy
```

#### Generate an ER diagram from your SQLite database:
``` bash
eralchemy -i sqlite:///instance/dev.db -o db_schema.png
```
**Options:**
- `-i` - input database URI (`sqlite:///path/to/db`)
- `-o` - output image file (`.png`, `.pdf`, or `.svg`)

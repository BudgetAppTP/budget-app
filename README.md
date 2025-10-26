# Budget Tracker App
Personal finance tracker for budgeting, expense tracking, and goal setting.

## Run the App
### Using the Makefile _(Simple)_
This project includes a `Makefile` to simplify common tasks such as setting up
a virtual environment, running the project, running tests, and cleaning up
temporary files.

- Install `make` on Linux _(Ubuntu)_:
``` bash
sudo apt update
sudo apt install build-essential
```
- Install `make` on Windows: [Link](https://stackoverflow.com/a/32127632)

#### Available Targets
| Target | Description |
|--------|-------------|
| `help` | Show the help message listing all targets. |
| `venv` | Create a virtual environment (if it doesn't exist) and install dependencies from `requirements.txt`. |
| `run`  | Run the project using the virtual environment Python interpreter. |
| `test` | Run tests using `pytest` inside the virtual environment. |
| `clean`| Remove the virtual environment and all `__pycache__` directories. |

### Basic Usage
1. Create virtual environment and install all required dependencies:
``` bash
make venv
```
2. Run the project:
``` bash
make run
```
> [!WARNING]
> **For Windows users:**
> - The Makefile works best in a **POSIX-compatible shell** such as **Git Bash** or **WSL**.
> - If running from the default `cmd.exe` shell, some targets (like `venv` creation and cleanup) may not work correctly.


### Custom Run
1. Setup virtual environment:
```bash
python -m venv .venv
pip install -r requirements.txt
```
2. Create `.env` for custom configuration. _(Optional)_
``` bash
cp .env.example .env
```

3. Run the app:
``` bash
python run.py
```

### Project Structure

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


### Notes

* Optional import from Excel: set `IMPORT_XLSX_PATH` in `.env` (ignored if file not found).

## API Documentation
 The REST API endpoints are documented and can be explored via Swagger UI.

After starting the app, open this URL in your browser:

http://127.0.0.1:5000/api/docs

It provides interactive documentation for REST endpoints (incomes, receipts).


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

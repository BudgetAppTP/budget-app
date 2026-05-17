# Budget Tracker App

![Backend Flask](https://img.shields.io/badge/backend-Flask-000000?logo=flask)
![Frontend React + Vite](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB?logo=react&logoColor=white)
![Database PostgreSQL + SQLite](https://img.shields.io/badge/database-PostgreSQL%20%2B%20SQLite-336791?logo=postgresql&logoColor=white)
![Tests Pytest](https://img.shields.io/badge/tests-Pytest-0A9EDC?logo=pytest&logoColor=white)

Budget Tracker is a full-stack budgeting application with a Flask JSON API and a React single-page frontend. This repository is organized so a client can review the finished solution quickly, while developers still have dedicated deep-dive documentation for the frontend and backend.

## Quick Start (Recommended)

This is the fastest way to run the full app locally for review.

1. Create a local environment file:

   ```bash
   cp .env.example .env
   ```

   Windows users can copy the file manually or use `copy .env.example .env` in `cmd.exe`.

2. Start the development Docker stack:

   ```bash
   make docker-up
   ```

3. Open the app:
   - App: `http://localhost:5173`
   - Swagger UI: `http://localhost:5173/api/docs`

4. When prompted by the browser, sign in with the HTTP Basic Auth credentials from `.env`:
   - `BASIC_AUTH_USER`
   - `BASIC_AUTH_PASSWORD`

   The sample values in `.env.example` are `admin` / `change-me`.

## Prerequisites

- Docker with Docker Compose support
- `make` for the convenience commands in the project root

If you are on Windows, `make` is most reliable in WSL or Git Bash.

## What To Review

- The React SPA for budgeting, expenses, incomes, savings, and dashboards
- The Flask JSON API under `/api/*`
- The live Swagger documentation at `/api/docs`
- The automated backend test suite run with `pytest`

## Run Tests

From the project root:

```bash
make test
```

More testing detail lives in [tests/README.md](tests/README.md).

## Architecture At a Glance

```text
budget-app/
├── app/      Flask API, services, models, config, deployment notes
├── client/   React + Vite frontend
├── tests/    Backend test suite
└── docs/     Project documentation sources
```

- Frontend deep dive: [client/README.md](client/README.md)
- Backend deep dive: [app/README.md](app/README.md)

## Local Development (Optional)

If you prefer to run the app without Docker, start the backend and frontend separately.

Backend:

```bash
make venv
make run
```

Frontend:

```bash
cd client
npm install
npm run dev
```

Local URLs:

- Frontend: `http://localhost:5173`
- Backend API: `http://127.0.0.1:5000/api`
- Swagger UI: `http://127.0.0.1:5000/api/docs`

## Additional Docs

- [client/README.md](client/README.md)
- [app/README.md](app/README.md)
- [tests/README.md](tests/README.md)
- [docs/README.md](docs/README.md)

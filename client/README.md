# Budget App Frontend

React single-page application for the Budget Tracker API. The client is built with Vite and talks
to the Flask backend through `/api/*`.

## Local Development

From `client/`:

```bash
npm install
npm run dev
```

By default, Vite opens `http://localhost:5173`. The dev proxy forwards `/api/*` to
`VITE_PROXY_TARGET` (default in Docker compose: `http://backend:5000`; for a local backend outside
Docker use `http://localhost:5000`).

## Docker

The root `docker-compose.yaml` builds the frontend with `client/Dockerfile.dev` and runs it behind
the local `external-nginx` service. This mirrors the production shape: browser traffic enters
through nginx, frontend serves the SPA, and `/api/*` is routed to the backend.

Production images are built by `.github/workflows/deploy-prod-services.yml` with
`client/Dockerfile.prod` and `VITE_API_URL=/api`.

## Useful Commands

```bash
npm run dev
npm run build
npm run lint
```

The repository currently relies on backend tests in CI; frontend checks can be run manually with
the npm scripts above.

# Frontend README

This folder contains the React single-page application for Budget Tracker. It is built with Vite, talks to the backend through `/api`, and is the main UI that reviewers see when they open the app in the browser.

## Local Setup

From the `client/` directory:

```bash
npm install
npm run dev
```

The Vite dev server runs on `http://localhost:5173` by default.

If the backend is running directly on your machine, the dev proxy targets `http://localhost:5000` unless you override it. In Docker development, the proxy target is set to `http://backend:5000`.

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite development server |
| `npm run build` | Run TypeScript build checks and create a production bundle |
| `npm run lint` | Run ESLint |
| `npm run preview` | Preview the production build locally |

## Environment Variables

The frontend uses these variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | `/api` | Base URL used by the built frontend for API calls |
| `VITE_PROXY_TARGET` | `http://localhost:5000` locally | Target for the Vite development proxy |
| `VITE_GOOGLE_CLIENT_ID` | empty | Enables Google sign-in in the UI when paired with backend config |

The sample frontend environment file is [client/.env.example](./.env.example).

## API Proxy Behavior

During local development, the browser talks to the Vite server first. Requests to `/api/*` are then proxied by Vite to the backend.

- Local backend outside Docker: set `VITE_PROXY_TARGET=http://localhost:5000`
- Backend inside Docker Compose: use `VITE_PROXY_TARGET=http://backend:5000`

This keeps frontend code stable because the app can keep calling `/api/*` in both cases.

## Build and Deployment Notes

- Development container: [client/Dockerfile.dev](./Dockerfile.dev) runs the Vite dev server on port `5173`
- Production container: [client/Dockerfile.prod](./Dockerfile.prod) builds static assets and serves them through nginx on port `80`
- Production builds use `VITE_API_URL=/api`, so the deployed frontend expects the reverse proxy to expose backend routes under the same origin

Backend and deployment details are documented in [app/README.md](../app/README.md).

## Troubleshooting

### API requests fail in local development

Check `VITE_PROXY_TARGET` first. A frontend running on `localhost:5173` cannot reach the backend if the proxy points to the wrong host or port.

### Google login button appears but authentication fails

Make sure `VITE_GOOGLE_CLIENT_ID` in the frontend matches `GOOGLE_CLIENT_ID` in the backend configuration. The frontend obtains the ID token, and the backend validates it against the configured audience.

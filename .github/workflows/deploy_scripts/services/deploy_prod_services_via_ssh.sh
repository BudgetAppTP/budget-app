#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_SSH_HOST:?DEPLOY_SSH_HOST is required}"
: "${DEPLOY_SSH_USER:?DEPLOY_SSH_USER is required}"
: "${DEPLOY_SSH_KEY_PATH:?DEPLOY_SSH_KEY_PATH is required}"
: "${REMOTE_APP_DIR:?REMOTE_APP_DIR is required}"
: "${DEPLOY_REPO_URL:?DEPLOY_REPO_URL is required}"
: "${GHCR_USERNAME:?GHCR_USERNAME is required}"
: "${GHCR_TOKEN:?GHCR_TOKEN is required}"
: "${BACKEND_IMAGE:?BACKEND_IMAGE is required}"
: "${FRONTEND_IMAGE:?FRONTEND_IMAGE is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${SECRET_KEY:?SECRET_KEY is required}"

DEPLOY_SSH_PORT="${DEPLOY_SSH_PORT:-22}"
DEPLOY_REF="${DEPLOY_REF:-main}"
DEPLOY_GIT_REMOTE="${DEPLOY_GIT_REMOTE:-origin}"
PROD_DOCKER_NETWORK="${PROD_DOCKER_NETWORK:-budget-prod-network}"
GHCR_TOKEN_B64="$(printf '%s' "${GHCR_TOKEN}" | base64 -w 0)"
POSTGRES_USER_B64="$(printf '%s' "${POSTGRES_USER}" | base64 -w 0)"
POSTGRES_PASSWORD_B64="$(printf '%s' "${POSTGRES_PASSWORD}" | base64 -w 0)"
POSTGRES_DB_B64="$(printf '%s' "${POSTGRES_DB}" | base64 -w 0)"
SECRET_KEY_B64="$(printf '%s' "${SECRET_KEY}" | base64 -w 0)"
DEPLOY_REPO_URL_B64="$(printf '%s' "${DEPLOY_REPO_URL}" | base64 -w 0)"

SSH_OPTS=(
  -i "${DEPLOY_SSH_KEY_PATH}"
  -p "${DEPLOY_SSH_PORT}"
  -o StrictHostKeyChecking=accept-new
  -o UserKnownHostsFile=~/.ssh/known_hosts
)

ssh "${SSH_OPTS[@]}" "${DEPLOY_SSH_USER}@${DEPLOY_SSH_HOST}" \
  "bash -s -- '${REMOTE_APP_DIR}' '${DEPLOY_REF}' '${DEPLOY_GIT_REMOTE}' '${PROD_DOCKER_NETWORK}' '${GHCR_USERNAME}' '${GHCR_TOKEN_B64}' '${BACKEND_IMAGE}' '${FRONTEND_IMAGE}' '${POSTGRES_USER_B64}' '${POSTGRES_PASSWORD_B64}' '${POSTGRES_DB_B64}' '${SECRET_KEY_B64}' '${DEPLOY_REPO_URL_B64}'" \
  < .github/workflows/deploy_scripts/services/remote_deploy_prod_services.sh

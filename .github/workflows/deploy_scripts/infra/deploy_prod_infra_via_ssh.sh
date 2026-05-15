#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_SSH_HOST:?DEPLOY_SSH_HOST is required}"
: "${DEPLOY_SSH_USER:?DEPLOY_SSH_USER is required}"
: "${DEPLOY_SSH_KEY_PATH:?DEPLOY_SSH_KEY_PATH is required}"
: "${REMOTE_APP_DIR:?REMOTE_APP_DIR is required}"
: "${DEPLOY_REPO_URL:?DEPLOY_REPO_URL is required}"
: "${GHCR_USERNAME:?GHCR_USERNAME is required}"
: "${GHCR_TOKEN:?GHCR_TOKEN is required}"
: "${EXTERNAL_NGINX_IMAGE:?EXTERNAL_NGINX_IMAGE is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${BASIC_AUTH_USER:?BASIC_AUTH_USER is required}"
: "${BASIC_AUTH_PASSWORD:?BASIC_AUTH_PASSWORD is required}"

DEPLOY_SSH_PORT="${DEPLOY_SSH_PORT:-22}"
DEPLOY_REF="${DEPLOY_REF:-main}"
DEPLOY_GIT_REMOTE="${DEPLOY_GIT_REMOTE:-origin}"
PROD_DOCKER_NETWORK="${PROD_DOCKER_NETWORK:-budget-prod-network}"
INFRA_TARGET="${INFRA_TARGET:-both}"
GHCR_TOKEN_B64="$(printf '%s' "${GHCR_TOKEN}" | base64 -w 0)"
POSTGRES_USER_B64="$(printf '%s' "${POSTGRES_USER}" | base64 -w 0)"
POSTGRES_PASSWORD_B64="$(printf '%s' "${POSTGRES_PASSWORD}" | base64 -w 0)"
POSTGRES_DB_B64="$(printf '%s' "${POSTGRES_DB}" | base64 -w 0)"
BASIC_AUTH_USER_B64="$(printf '%s' "${BASIC_AUTH_USER}" | base64 -w 0)"
BASIC_AUTH_PASSWORD_B64="$(printf '%s' "${BASIC_AUTH_PASSWORD}" | base64 -w 0)"
DEPLOY_REPO_URL_B64="$(printf '%s' "${DEPLOY_REPO_URL}" | base64 -w 0)"

SSH_OPTS=(
  -i "${DEPLOY_SSH_KEY_PATH}"
  -p "${DEPLOY_SSH_PORT}"
  -o StrictHostKeyChecking=accept-new
  -o UserKnownHostsFile=~/.ssh/known_hosts
)

ssh "${SSH_OPTS[@]}" "${DEPLOY_SSH_USER}@${DEPLOY_SSH_HOST}" \
  "bash -s -- '${REMOTE_APP_DIR}' '${DEPLOY_REF}' '${DEPLOY_GIT_REMOTE}' '${PROD_DOCKER_NETWORK}' '${INFRA_TARGET}' '${GHCR_USERNAME}' '${GHCR_TOKEN_B64}' '${EXTERNAL_NGINX_IMAGE}' '${POSTGRES_USER_B64}' '${POSTGRES_PASSWORD_B64}' '${POSTGRES_DB_B64}' '${BASIC_AUTH_USER_B64}' '${BASIC_AUTH_PASSWORD_B64}' '${DEPLOY_REPO_URL_B64}'" \
  < .github/workflows/deploy_scripts/infra/remote_deploy_prod_infra.sh

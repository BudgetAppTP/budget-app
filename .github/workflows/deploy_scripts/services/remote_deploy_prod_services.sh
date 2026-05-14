#!/usr/bin/env bash
set -euo pipefail

REMOTE_APP_DIR="${1:?remote app dir is required}"
DEPLOY_REF="${2:?deploy ref is required}"
DEPLOY_GIT_REMOTE="${3:?deploy git remote is required}"
PROD_DOCKER_NETWORK="${4:?prod docker network is required}"
GHCR_USERNAME="${5:?ghcr username is required}"
GHCR_TOKEN_B64="${6:?ghcr token (base64) is required}"
BACKEND_IMAGE="${7:?backend image is required}"
FRONTEND_IMAGE="${8:?frontend image is required}"
POSTGRES_USER_B64="${9:?postgres user (base64) is required}"
POSTGRES_PASSWORD_B64="${10:?postgres password (base64) is required}"
POSTGRES_DB_B64="${11:?postgres db (base64) is required}"
SECRET_KEY_B64="${12:?secret key (base64) is required}"
DEPLOY_REPO_URL_B64="${13:?deploy repo url (base64) is required}"
GHCR_TOKEN="$(printf '%s' "${GHCR_TOKEN_B64}" | base64 -d)"
POSTGRES_USER="$(printf '%s' "${POSTGRES_USER_B64}" | base64 -d)"
POSTGRES_PASSWORD="$(printf '%s' "${POSTGRES_PASSWORD_B64}" | base64 -d)"
POSTGRES_DB="$(printf '%s' "${POSTGRES_DB_B64}" | base64 -d)"
SECRET_KEY="$(printf '%s' "${SECRET_KEY_B64}" | base64 -d)"
DEPLOY_REPO_URL="$(printf '%s' "${DEPLOY_REPO_URL_B64}" | base64 -d)"

git_with_auth() {
  local auth_b64
  auth_b64="$(printf 'x-access-token:%s' "${GHCR_TOKEN}" | base64 | tr -d '\n')"
  git -c "http.extraheader=AUTHORIZATION: basic ${auth_b64}" "$@"
}

find_docker_bin() {
  if command -v docker >/dev/null 2>&1; then
    command -v docker
    return 0
  fi
  if [ -x /snap/bin/docker ]; then
    echo "/snap/bin/docker"
    return 0
  fi
  return 1
}

DOCKER_BIN="$(find_docker_bin || true)"
if [ -z "${DOCKER_BIN}" ]; then
  echo "ERROR: docker is not installed (or not in PATH) on remote host"
  exit 127
fi

DOCKER_PREFIX=()
if ! "${DOCKER_BIN}" info >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1 && sudo -n "${DOCKER_BIN}" info >/dev/null 2>&1; then
    DOCKER_PREFIX=(sudo -n)
  else
    echo "ERROR: no access to Docker daemon for current user"
    echo "Hint: add deploy user to 'docker' group or allow passwordless sudo for docker"
    exit 126
  fi
fi

docker_cmd() {
  if [ "${#DOCKER_PREFIX[@]}" -gt 0 ]; then
    "${DOCKER_PREFIX[@]}" env \
      "BACKEND_IMAGE=${BACKEND_IMAGE-}" \
      "FRONTEND_IMAGE=${FRONTEND_IMAGE-}" \
      "PROD_DOCKER_NETWORK=${PROD_DOCKER_NETWORK-}" \
      "POSTGRES_USER=${POSTGRES_USER-}" \
      "POSTGRES_PASSWORD=${POSTGRES_PASSWORD-}" \
      "POSTGRES_DB=${POSTGRES_DB-}" \
      "SECRET_KEY=${SECRET_KEY-}" \
      "${DOCKER_BIN}" "$@"
    return
  fi
  "${DOCKER_BIN}" "$@"
}

if [ ! -d "${REMOTE_APP_DIR}" ]; then
  mkdir -p "${REMOTE_APP_DIR}"
fi

REMOTE_APP_DIR="$(cd "${REMOTE_APP_DIR}" && pwd -P)"
STATE_DIR="${REMOTE_APP_DIR}/.deploy_state"
mkdir -p "${STATE_DIR}"

if [ ! -d "${REMOTE_APP_DIR}/.git" ]; then
  echo "[services] Bootstrapping git repository in ${REMOTE_APP_DIR}"
  git init "${REMOTE_APP_DIR}"
fi

cd "${REMOTE_APP_DIR}"

if git remote get-url "${DEPLOY_GIT_REMOTE}" >/dev/null 2>&1; then
  git remote set-url "${DEPLOY_GIT_REMOTE}" "${DEPLOY_REPO_URL}"
else
  git remote add "${DEPLOY_GIT_REMOTE}" "${DEPLOY_REPO_URL}"
fi

echo "[services] Syncing repository to ref: ${DEPLOY_REF}"
git_with_auth fetch "${DEPLOY_GIT_REMOTE}" --tags
if git rev-parse --verify "${DEPLOY_GIT_REMOTE}/${DEPLOY_REF}^{commit}" >/dev/null 2>&1; then
  git checkout -B "${DEPLOY_REF}" "${DEPLOY_GIT_REMOTE}/${DEPLOY_REF}"
elif git rev-parse --verify "${DEPLOY_REF}^{commit}" >/dev/null 2>&1; then
  git checkout --detach "${DEPLOY_REF}"
else
  echo "ERROR: deploy ref '${DEPLOY_REF}' not found"
  exit 1
fi

if ! docker_cmd network inspect "${PROD_DOCKER_NETWORK}" >/dev/null 2>&1; then
  echo "[services] Creating missing docker network: ${PROD_DOCKER_NETWORK}"
  docker_cmd network create "${PROD_DOCKER_NETWORK}"
fi

echo "[services] Logging in to GHCR"
printf '%s' "${GHCR_TOKEN}" | docker_cmd login ghcr.io -u "${GHCR_USERNAME}" --password-stdin

export BACKEND_IMAGE FRONTEND_IMAGE PROD_DOCKER_NETWORK
export POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB SECRET_KEY
COMPOSE_FILE="docker-compose-prod-services.yml"

declare -A SERVICE_HASH

calc_paths_hash() {
  local base_ref="$1"
  shift
  (
    for p in "$@"; do
      if git cat-file -e "${base_ref}:${p}" 2>/dev/null; then
        printf '%s ' "$p"
        git rev-parse "${base_ref}:${p}"
      else
        printf '%s %s\n' "$p" "MISSING"
      fi
    done
  ) | sha256sum | awk '{print $1}'
}

get_image_name_for_service() {
  local service="$1"
  mapfile -t _services < <(docker_cmd compose -f "${COMPOSE_FILE}" config --services)
  mapfile -t _images < <(docker_cmd compose -f "${COMPOSE_FILE}" config --images)
  local i
  for i in "${!_services[@]}"; do
    if [ "${_services[$i]}" = "${service}" ]; then
      echo "${_images[$i]}"
      return 0
    fi
  done
  return 1
}

should_deploy_service() {
  local service="$1"
  local service_hash="$2"
  local state_file="${STATE_DIR}/${service}.sha"
  local prev_hash=""
  if [ -f "${state_file}" ]; then
    prev_hash="$(cat "${state_file}")"
  fi

  local reason=""

  if [ "${prev_hash}" != "${service_hash}" ]; then
    reason="hash_changed"
  fi

  local container_id
  container_id="$(docker_cmd compose -f "${COMPOSE_FILE}" ps -q "${service}" || true)"
  if [ -z "${container_id}" ]; then
    reason="${reason:+${reason},}container_missing"
  fi

  echo "[services] Pulling image for ${service}"
  PROD_DOCKER_NETWORK="${PROD_DOCKER_NETWORK}" docker_cmd compose -f "${COMPOSE_FILE}" pull "${service}"

  local image_name
  image_name="$(get_image_name_for_service "${service}")"
  local pulled_image_id
  pulled_image_id="$(docker_cmd image inspect -f '{{.Id}}' "${image_name}")"

  if [ -n "${container_id}" ]; then
    local running_image_id
    running_image_id="$(docker_cmd inspect -f '{{.Image}}' "${container_id}")"
    if [ "${running_image_id}" != "${pulled_image_id}" ]; then
      reason="${reason:+${reason},}image_hash_changed"
    fi
  fi

  if [ -n "${reason}" ]; then
    echo "[services] ${service}: deploy needed (${reason})"
    return 0
  fi

  echo "[services] ${service}: no changes"
  return 1
}

SERVICE_HASH[backend]="$(calc_paths_hash HEAD \
  app \
  app/Dockerfile \
  app/requirements.txt \
  app/scripts/docker-entrypoint.sh \
  docker-compose-prod-services.yml)"

SERVICE_HASH[frontend]="$(calc_paths_hash HEAD \
  client \
  client/Dockerfile.prod \
  client/nginx.conf \
  docker-compose-prod-services.yml)"

SERVICES_TO_DEPLOY=()

if should_deploy_service backend "${SERVICE_HASH[backend]}"; then
  SERVICES_TO_DEPLOY+=(backend)
fi

if should_deploy_service frontend "${SERVICE_HASH[frontend]}"; then
  SERVICES_TO_DEPLOY+=(frontend)
fi

if [ "${#SERVICES_TO_DEPLOY[@]}" -eq 0 ]; then
  echo "[services] No service changes detected. Skipping deploy."
  exit 0
fi

echo "[services] Deploying: ${SERVICES_TO_DEPLOY[*]}"
PROD_DOCKER_NETWORK="${PROD_DOCKER_NETWORK}" docker_cmd compose -f "${COMPOSE_FILE}" up -d --no-build "${SERVICES_TO_DEPLOY[@]}"

for s in "${SERVICES_TO_DEPLOY[@]}"; do
  echo "${SERVICE_HASH[$s]}" > "${STATE_DIR}/${s}.sha"
done

PROD_DOCKER_NETWORK="${PROD_DOCKER_NETWORK}" docker_cmd compose -f "${COMPOSE_FILE}" ps

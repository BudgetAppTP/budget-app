#!/usr/bin/env bash
set -euo pipefail

REMOTE_APP_DIR="${1:?remote app dir is required}"
DEPLOY_REF="${2:?deploy ref is required}"
DEPLOY_GIT_REMOTE="${3:?deploy git remote is required}"
PROD_DOCKER_NETWORK="${4:?prod docker network is required}"
INFRA_TARGET="${5:?infra target is required}"
GHCR_USERNAME="${6:?ghcr username is required}"
GHCR_TOKEN_B64="${7:?ghcr token (base64) is required}"
EXTERNAL_NGINX_IMAGE="${8:?external nginx image is required}"
POSTGRES_USER_B64="${9:?postgres user (base64) is required}"
POSTGRES_PASSWORD_B64="${10:?postgres password (base64) is required}"
POSTGRES_DB_B64="${11:?postgres db (base64) is required}"
BASIC_AUTH_USER_B64="${12:?basic auth user (base64) is required}"
BASIC_AUTH_PASSWORD_B64="${13:?basic auth password (base64) is required}"
DEPLOY_REPO_URL_B64="${14:?deploy repo url (base64) is required}"
GHCR_TOKEN="$(printf '%s' "${GHCR_TOKEN_B64}" | base64 -d)"
POSTGRES_USER="$(printf '%s' "${POSTGRES_USER_B64}" | base64 -d)"
POSTGRES_PASSWORD="$(printf '%s' "${POSTGRES_PASSWORD_B64}" | base64 -d)"
POSTGRES_DB="$(printf '%s' "${POSTGRES_DB_B64}" | base64 -d)"
BASIC_AUTH_USER="$(printf '%s' "${BASIC_AUTH_USER_B64}" | base64 -d)"
BASIC_AUTH_PASSWORD="$(printf '%s' "${BASIC_AUTH_PASSWORD_B64}" | base64 -d)"
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
      "EXTERNAL_NGINX_IMAGE=${EXTERNAL_NGINX_IMAGE-}" \
      "PROD_DOCKER_NETWORK=${PROD_DOCKER_NETWORK-}" \
      "POSTGRES_USER=${POSTGRES_USER-}" \
      "POSTGRES_PASSWORD=${POSTGRES_PASSWORD-}" \
      "POSTGRES_DB=${POSTGRES_DB-}" \
      "BASIC_AUTH_USER=${BASIC_AUTH_USER-}" \
      "BASIC_AUTH_PASSWORD=${BASIC_AUTH_PASSWORD-}" \
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
  echo "[infra] Bootstrapping git repository in ${REMOTE_APP_DIR}"
  git init "${REMOTE_APP_DIR}"
fi

cd "${REMOTE_APP_DIR}"

if git remote get-url "${DEPLOY_GIT_REMOTE}" >/dev/null 2>&1; then
  git remote set-url "${DEPLOY_GIT_REMOTE}" "${DEPLOY_REPO_URL}"
else
  git remote add "${DEPLOY_GIT_REMOTE}" "${DEPLOY_REPO_URL}"
fi

echo "[infra] Syncing repository to ref: ${DEPLOY_REF}"
git_with_auth fetch "${DEPLOY_GIT_REMOTE}" --tags
if git rev-parse --verify "${DEPLOY_GIT_REMOTE}/${DEPLOY_REF}^{commit}" >/dev/null 2>&1; then
  git checkout -B "${DEPLOY_REF}" "${DEPLOY_GIT_REMOTE}/${DEPLOY_REF}"
elif git rev-parse --verify "${DEPLOY_REF}^{commit}" >/dev/null 2>&1; then
  git checkout --detach "${DEPLOY_REF}"
else
  echo "ERROR: deploy ref '${DEPLOY_REF}' not found"
  exit 1
fi

echo "[infra] Logging in to GHCR"
printf '%s' "${GHCR_TOKEN}" | docker_cmd login ghcr.io -u "${GHCR_USERNAME}" --password-stdin

export EXTERNAL_NGINX_IMAGE PROD_DOCKER_NETWORK
export POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB
export BASIC_AUTH_USER BASIC_AUTH_PASSWORD
COMPOSE_FILE="docker-compose-prod-infra.yml"
PROJECT_NAME="budget-infra"

declare -A TARGET_HASH

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
  mapfile -t _services < <(docker_cmd compose --project-name "${PROJECT_NAME}" -f "${COMPOSE_FILE}" config --services)
  mapfile -t _images < <(docker_cmd compose --project-name "${PROJECT_NAME}" -f "${COMPOSE_FILE}" config --images)
  local i
  for i in "${!_services[@]}"; do
    if [ "${_services[$i]}" = "${service}" ]; then
      echo "${_images[$i]}"
      return 0
    fi
  done
  return 1
}

need_deploy_postgres() {
  local pg_hash="$1"
  local state_file="${STATE_DIR}/infra_postgres.sha"
  local prev_hash=""
  if [ -f "${state_file}" ]; then
    prev_hash="$(cat "${state_file}")"
  fi

  local reason=""
  if [ "${prev_hash}" != "${pg_hash}" ]; then
    reason="hash_changed"
  fi

  local cid
  cid="$(docker_cmd compose --project-name "${PROJECT_NAME}" -f "${COMPOSE_FILE}" ps -q db || true)"
  if [ -z "${cid}" ]; then
    reason="${reason:+${reason},}container_missing"
  fi

  docker_cmd compose --project-name "${PROJECT_NAME}" -f "${COMPOSE_FILE}" pull db

  local desired_image_id
  desired_image_id="$(docker_cmd image inspect -f '{{.Id}}' postgres:17.5-alpine)"

  if [ -n "${cid}" ]; then
    local running_image_id
    running_image_id="$(docker_cmd inspect -f '{{.Image}}' "${cid}")"
    if [ "${running_image_id}" != "${desired_image_id}" ]; then
      reason="${reason:+${reason},}image_hash_changed"
    fi
  fi

  if [ -n "${reason}" ]; then
    echo "[infra] db: deploy needed (${reason})"
    return 0
  fi

  echo "[infra] db: no changes"
  return 1
}

need_deploy_nginx() {
  local ngx_hash="$1"
  local state_file="${STATE_DIR}/infra_nginx.sha"
  local prev_hash=""
  if [ -f "${state_file}" ]; then
    prev_hash="$(cat "${state_file}")"
  fi

  local reason=""
  if [ "${prev_hash}" != "${ngx_hash}" ]; then
    reason="hash_changed"
  fi

  local cid
  cid="$(docker_cmd compose --project-name "${PROJECT_NAME}" -f "${COMPOSE_FILE}" ps -q external-nginx || true)"
  if [ -z "${cid}" ]; then
    reason="${reason:+${reason},}container_missing"
  fi

  docker_cmd compose --project-name "${PROJECT_NAME}" -f "${COMPOSE_FILE}" pull external-nginx

  local image_name
  image_name="$(get_image_name_for_service external-nginx)"
  local pulled_image_id
  pulled_image_id="$(docker_cmd image inspect -f '{{.Id}}' "${image_name}")"

  if [ -n "${cid}" ]; then
    local running_image_id
    running_image_id="$(docker_cmd inspect -f '{{.Image}}' "${cid}")"
    if [ "${running_image_id}" != "${pulled_image_id}" ]; then
      reason="${reason:+${reason},}image_hash_changed"
    fi
  fi

  if [ -n "${reason}" ]; then
    echo "[infra] external-nginx: deploy needed (${reason})"
    return 0
  fi

  echo "[infra] external-nginx: no changes"
  return 1
}

TARGET_HASH[postgres]="$(calc_paths_hash HEAD docker-compose-prod-infra.yml)"
TARGET_HASH[nginx]="$(calc_paths_hash HEAD docker-compose-prod-infra.yml infra/external-nginx)"

TARGETS=()
case "${INFRA_TARGET}" in
  postgres)
    TARGETS=(postgres)
    ;;
  nginx)
    TARGETS=(nginx)
    ;;
  both)
    TARGETS=(postgres nginx)
    ;;
  *)
    echo "ERROR: INFRA_TARGET must be one of: postgres, nginx, both"
    exit 1
    ;;
esac

SERVICES_TO_DEPLOY=()
for t in "${TARGETS[@]}"; do
  if [ "${t}" = "postgres" ] && need_deploy_postgres "${TARGET_HASH[postgres]}"; then
    SERVICES_TO_DEPLOY+=(db)
  fi
  if [ "${t}" = "nginx" ] && need_deploy_nginx "${TARGET_HASH[nginx]}"; then
    SERVICES_TO_DEPLOY+=(external-nginx)
  fi
done

if [ "${#SERVICES_TO_DEPLOY[@]}" -eq 0 ]; then
  echo "[infra] No infrastructure changes detected. Skipping deploy."
  exit 0
fi

echo "[infra] Deploying: ${SERVICES_TO_DEPLOY[*]}"
PROD_DOCKER_NETWORK="${PROD_DOCKER_NETWORK}" docker_cmd compose --project-name "${PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d --no-build "${SERVICES_TO_DEPLOY[@]}"

for t in "${TARGETS[@]}"; do
  if [ "${t}" = "postgres" ] && printf '%s\n' "${SERVICES_TO_DEPLOY[@]}" | grep -qx "db"; then
    echo "${TARGET_HASH[postgres]}" > "${STATE_DIR}/infra_postgres.sha"
  fi
  if [ "${t}" = "nginx" ] && printf '%s\n' "${SERVICES_TO_DEPLOY[@]}" | grep -qx "external-nginx"; then
    echo "${TARGET_HASH[nginx]}" > "${STATE_DIR}/infra_nginx.sha"
  fi
done

PROD_DOCKER_NETWORK="${PROD_DOCKER_NETWORK}" docker_cmd compose --project-name "${PROJECT_NAME}" -f "${COMPOSE_FILE}" ps

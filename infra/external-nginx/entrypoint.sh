#!/bin/sh
set -eu

if [ -z "${BASIC_AUTH_USER:-}" ] || [ -z "${BASIC_AUTH_PASSWORD:-}" ]; then
  echo "ERROR: BASIC_AUTH_USER and BASIC_AUTH_PASSWORD must be set"
  exit 1
fi

if [ -z "${FRONTEND_UPSTREAM:-}" ]; then
  echo "ERROR: FRONTEND_UPSTREAM must be set (example: frontend:80)"
  exit 1
fi

BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-backend:5000}"

htpasswd -bc /etc/nginx/.htpasswd "$BASIC_AUTH_USER" "$BASIC_AUTH_PASSWORD"

envsubst '${FRONTEND_UPSTREAM} ${BACKEND_UPSTREAM}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'

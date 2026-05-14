FROM nginx:1.27-alpine

RUN apk add --no-cache apache2-utils gettext

COPY infra/external-nginx/entrypoint.sh /entrypoint.sh
COPY infra/external-nginx/default.conf.template /etc/nginx/templates/default.conf.template

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

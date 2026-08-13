#!/usr/bin/env sh
set -eu

: "${DJANGO_SECRET_KEY:?DJANGO_SECRET_KEY must be set}"
: "${DJANGO_ALLOWED_HOSTS:?DJANGO_ALLOWED_HOSTS must be set}"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "${DJANGO_DEBUG:-true}" != "false" ]; then
    echo "DJANGO_DEBUG must be false for deployment checks" >&2
    exit 1
fi

python "$SCRIPT_DIR/../manage.py" check --deploy

#!/usr/bin/env sh
set -eu

echo "[entrypoint] running migrations..."
python manage.py migrate --noinput

if [ "${DJANGO_COLLECTSTATIC:-0}" = "1" ]; then
  echo "[entrypoint] collectstatic..."
  python manage.py collectstatic --noinput
fi

echo "[entrypoint] starting django..."
exec python manage.py runserver 0.0.0.0:8000



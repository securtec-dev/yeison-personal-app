#!/bin/sh
set -e

if [ "$1" = "gunicorn" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  python manage.py seed_initial_data
fi

if [ "$(id -u)" = "0" ]; then
  mkdir -p /app/media /app/staticfiles
  chown -R app:app /app/media /app/staticfiles 2>/dev/null || true
  exec gosu app "$@"
fi

exec "$@"

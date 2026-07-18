#!/bin/sh
set -e

if [ "$#" -eq 0 ]; then
  case "${PROCESS_TYPE:-web}" in
    web)
      set -- gunicorn config.wsgi:application \
        --bind "0.0.0.0:${PORT:-8000}" \
        --workers "${WEB_CONCURRENCY:-2}" \
        --threads 4 \
        --timeout 120
      ;;
    worker)
      set -- celery -A config worker --loglevel=info --concurrency="${CELERY_CONCURRENCY:-2}"
      ;;
    scheduler)
      set -- celery -A config beat --loglevel=info --schedule=/tmp/celerybeat-schedule
      ;;
    *)
      echo "PROCESS_TYPE inválido: ${PROCESS_TYPE}" >&2
      exit 64
      ;;
  esac
fi

if [ "${PROCESS_TYPE:-web}" = "web" ] && [ "$1" = "gunicorn" ]; then
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

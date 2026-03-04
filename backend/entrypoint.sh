#!/bin/bash
set -e

echo "Waiting for database..."
while ! python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec gunicorn app.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -

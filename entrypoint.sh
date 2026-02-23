#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate

echo "Creating superuser if not exists..."
python scripts/create_superuser.py

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
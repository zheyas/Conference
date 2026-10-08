#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate

echo "Seeding initial conference data if needed..."
python manage.py seed_demo_data

echo "Creating superuser from .env if not exists..."
python scripts/create_superuser_from_env.py

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000

#!/bin/bash


set -e

echo "Running migrations.."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Compiling translations..."
python manage.py compilemessages

echo "Starting application..."

exec "$@"
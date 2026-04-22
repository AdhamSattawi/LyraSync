#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"

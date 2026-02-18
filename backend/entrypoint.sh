#!/bin/bash

echo "DB Connection --- Establishing . . ."

while ! nc -z db 5432; do

    echo "DB Connection -- Failed!"

    sleep 1

    echo "DB Connection -- Retrying . . ."

done

echo "DB Connection --- Successfully Established!"

echo "Running database migrations . . ."
alembic upgrade head
echo "Database migrations --- Done!"

echo "Seeding admin user . . ."
python -m src.seeders.seed_admin || echo "Admin seeder skipped (may already exist)"

exec "$@"

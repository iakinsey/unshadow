#!/bin/bash


service postgresql start

until su - postgres -c "psql -U \"postgres\" -c '\l'"; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up"

su - postgres -c "psql -f /tmp/setup_db.sql"
su - postgres -c "echo \"CREATE EXTENSION pg_trgm\" | psql -d unshadow"

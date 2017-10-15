#!/bin/bash


psql -f /tmp/


until psql -U "postgres" -c '\l'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up"

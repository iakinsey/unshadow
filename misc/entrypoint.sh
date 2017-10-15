#!/bin/bash

service tor start
#service nginx start
service postgresql start
service cron start

until su - postgres -c "psql -U \"postgres\" -c '\l'"; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

#source env/bin/activate && ./unshadow-metrics &
source env/bin/activate && ./unshadow-crawler

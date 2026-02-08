#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER chmusicpro WITH PASSWORD 'chmusicpro123';
    CREATE DATABASE chmusicpro OWNER chmusicpro;
    GRANT ALL PRIVILEGES ON DATABASE chmusicpro TO chmusicpro;
EOSQL

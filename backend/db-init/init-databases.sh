#!/bin/bash
set -euo pipefail

# Creates four logically separate databases (bkash_db, nagad_db, rocket_db,
# shared_db) and a dedicated, restricted-privilege role per database. Each
# role can only connect to and operate on its own database - a bkash-scoped
# connection has no grant to read nagad_db or rocket_db, enforcing provider
# boundaries at the Postgres permission layer, not just in application code.

create_db_and_role() {
  local db_name="$1"
  local role_name="$2"
  local role_password="$3"

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE ${db_name};
    CREATE ROLE ${role_name} WITH LOGIN PASSWORD '${role_password}';
    REVOKE ALL PRIVILEGES ON DATABASE ${db_name} FROM PUBLIC;
    GRANT ALL PRIVILEGES ON DATABASE ${db_name} TO ${role_name};
EOSQL

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${db_name}" <<-EOSQL
    GRANT ALL PRIVILEGES ON SCHEMA public TO ${role_name};
EOSQL
}

create_db_and_role "bkash_db"  "bkash_service"  "${BKASH_DB_PASSWORD:-bkash_pw}"
create_db_and_role "nagad_db"  "nagad_service"  "${NAGAD_DB_PASSWORD:-nagad_pw}"
create_db_and_role "rocket_db" "rocket_service" "${ROCKET_DB_PASSWORD:-rocket_pw}"
create_db_and_role "shared_db" "shared_service" "${SHARED_DB_PASSWORD:-shared_pw}"

# NOTE: sync-service's cross-database role (it needs read access to all three
# provider DBs plus write access to shared_db) is deliberately NOT created
# here yet. Its exact grants depend on tables that don't exist until Phase 2/3
# move real models in - adding it now, untestable, would just be a guess.
# Tracked for Phase 3 (sync-service implementation).

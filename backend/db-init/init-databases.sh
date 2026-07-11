#!/bin/bash
set -euo pipefail

# Creates five logically separate databases (bkash_db, nagad_db, rocket_db,
# shared_db, aggregator_db) and one restricted-privilege role per database,
# plus a sixth cross-cutting role (sync_service) for the Sync Service.
#
# Provider boundary: each provider role can only connect to its own
# database - enforced at the Postgres permission layer, not just in
# application code.
#
# shared_db write boundary: `shared_service` (aggregator-api's credential
# for the *projection* data) gets CONNECT + SELECT only - it can never write
# here. `sync_service` is the only role with write access to shared_db, and
# is also the only role (besides each provider's own service role) that can
# read the three provider databases - a deliberately separate credential
# from bkash_service/nagad_service/rocket_service, so even a compromised
# sync-service cannot write provider data.
#
# aggregator_db is a SEPARATE database for state that genuinely belongs to
# aggregator-api itself - users, alerts, cases - none of which is a
# provider-sync projection. Giving it its own database (with its own
# read-write role, `aggregator_service`) means the "only sync_service writes
# shared_db" rule never needs an exception: aggregator-api writes its own
# domain data to its own database, and only ever reads (never writes)
# shared_db via the separate, still-read-only `shared_service` credential.

create_provider_db_and_role() {
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

create_provider_db_and_role "bkash_db"  "bkash_service"  "${BKASH_DB_PASSWORD:-bkash_pw}"
create_provider_db_and_role "nagad_db"  "nagad_service"  "${NAGAD_DB_PASSWORD:-nagad_pw}"
create_provider_db_and_role "rocket_db" "rocket_service" "${ROCKET_DB_PASSWORD:-rocket_pw}"

# shared_db: created with only a CONNECT grant for shared_service - table-
# level SELECT is added below, once sync_service (the table owner) exists,
# via a default-privilege rule that applies to whatever sync_service creates.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE shared_db;
  CREATE ROLE shared_service WITH LOGIN PASSWORD '${SHARED_DB_PASSWORD:-shared_pw}';
  REVOKE ALL PRIVILEGES ON DATABASE shared_db FROM PUBLIC;
  GRANT CONNECT ON DATABASE shared_db TO shared_service;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE ROLE sync_service WITH LOGIN PASSWORD '${SYNC_SERVICE_DB_PASSWORD:-sync_pw}';
  GRANT CONNECT ON DATABASE bkash_db, nagad_db, rocket_db, shared_db TO sync_service;
  GRANT ALL PRIVILEGES ON DATABASE shared_db TO sync_service;
EOSQL

# Read-only access to each provider database for sync_service, scoped to
# whatever that provider's own service role creates (provider-api owns that
# schema; sync-service only ever reads it).
for role_db in "bkash_service:bkash_db" "nagad_service:nagad_db" "rocket_service:rocket_db"; do
  role="${role_db%%:*}"
  db="${role_db##*:}"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${db}" <<-EOSQL
    GRANT USAGE ON SCHEMA public TO sync_service;
    ALTER DEFAULT PRIVILEGES FOR ROLE ${role} IN SCHEMA public GRANT SELECT ON TABLES TO sync_service;
EOSQL
done

# sync_service owns (creates) the shared_db schema; shared_service
# (aggregator-api, Phase 5) gets SELECT-only on whatever sync_service creates.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "shared_db" <<-EOSQL
  GRANT ALL PRIVILEGES ON SCHEMA public TO sync_service;
  ALTER DEFAULT PRIVILEGES FOR ROLE sync_service IN SCHEMA public GRANT SELECT ON TABLES TO shared_service;
EOSQL

# aggregator_db: aggregator-api's own database (users, alerts, cases -
# Phase 6+). aggregator_service owns and fully controls this schema; no
# other role gets any access to it.
create_provider_db_and_role "aggregator_db" "aggregator_service" "${AGGREGATOR_DB_PASSWORD:-aggregator_pw}"

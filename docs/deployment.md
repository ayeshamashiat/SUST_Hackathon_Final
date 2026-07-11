# Deployment Guide

> v1 — written at Phase 1 of the backend refactor (Docker Compose infra
> scaffold only). Update this file every time deployment changes.

## Two backends currently coexist

This repo is mid-refactor. There are **two ways to run the backend right now**
— don't run both against port 8000 at the same time:

1. **Old (current default)**: single FastAPI process, SQLite, no Docker.
   Still what `backend/README.md` documents. Still what the frontend talks to
   today.
2. **New (Phase 1, not yet feature-complete)**: `docker compose` stack under
   `backend/` — Postgres with 4 databases + `provider-api` + `sync-service` +
   `aggregator-api`. As of Phase 1 these three services only expose `/health`;
   no business logic has moved over yet (that's Phase 2+).

Once Phase 6 lands, the old single-process backend will be decommissioned and
this file will drop the "two backends" framing.

## Running the new Docker Compose stack

```bash
cd backend
cp .env.example .env   # first time only
docker compose up --build
```

This starts 4 containers:

| Service | Host port | Purpose |
|---|---|---|
| `postgres` | 5433 (mapped; container listens on 5432) | One Postgres instance, 4 databases: `bkash_db`, `nagad_db`, `rocket_db`, `shared_db` |
| `provider-api` | 8001 (dev-only) | Owns bkash/nagad/rocket DB access. Not required by the frontend. |
| `sync-service` | 8002 (dev-only) | Polls provider DBs directly, projects into `shared_db`. Not required by the frontend. |
| `aggregator-api` | 8000 | The only service the frontend talks to. Reads `shared_db` only. |

Health checks:
```bash
curl http://localhost:8000/health   # aggregator-api
curl http://localhost:8001/health   # provider-api
curl http://localhost:8002/health   # sync-service
curl http://localhost:8002/sync/status   # sync-service: per-provider sync state + status counts (debug-only, not required by any spec)
```

## Container environment scoping (Phase 5)

Each of `provider-api`, `sync-service`, `aggregator-api` gets an explicit
`environment:` allow-list in `docker-compose.yml` - not `env_file: .env`.
A shared `env_file` would hand every service's credentials to every
container (e.g. `aggregator-api` would receive `nagad_service`'s full
read-write password even though its code never reads it), which quietly
weakens "aggregator must never query provider databases" down to "the code
doesn't currently do that" instead of "the credential to do that isn't even
present." `.env` at the project root is still the single source of values -
Docker Compose uses it for `${VAR}` substitution in the compose file, it's
just no longer injected wholesale into any container.

Verify a container's actual environment any time with:
```bash
docker compose exec aggregator-api env   # must show no BKASH_/NAGAD_/ROCKET_ variable
```

## Postgres roles (updated Phase 6)

Six roles now exist, each scoped to exactly what it needs - this is
enforced by Postgres `GRANT`/`REVOKE`, not just by which connection string a
service happens to be given:

| Role | Used by | Can read | Can write |
|---|---|---|---|
| `bkash_service` / `nagad_service` / `rocket_service` | provider-api | its own provider DB only | its own provider DB only |
| `sync_service` | sync-service | all 3 provider DBs (read-only) + `shared_db` | `shared_db` only - owns/creates its schema |
| `shared_service` | aggregator-api | `shared_db` only | nothing - `SELECT`-only, cannot `CREATE`/`INSERT`/`UPDATE` |
| `aggregator_service` | aggregator-api | `aggregator_db` only | `aggregator_db` only - owns/creates its own schema (users; alerts/cases from Phase 7) |

Note aggregator-api holds **two** credentials, not one: `shared_service`
(read-only, for the provider-sync projection) and `aggregator_service`
(read-write, for its own domain data). This is deliberate - see
`aggregator-api/app/db.py`'s module docstring - rather than punching a
write-access exception into `shared_db`'s "only sync-service writes here"
rule, aggregator-api gets a database it actually owns.

This is what makes "only the Sync Service may write to shared_db" and
"a provider router must never read another provider's database" real
guarantees rather than conventions - see the boundary checks below.

**If you already have a `pgdata` volume from before Phase 4/6**: `db-init/init-databases.sh` only runs on a database's *first* initialization, so an existing volume won't pick up new roles (`sync_service`, `aggregator_service`) or tightened grants automatically. Either:
- `docker compose down -v` (destructive - wipes all Postgres data, always confirm before running this), then `docker compose up --build`, or
- apply the equivalent grants live against the running container (see the SQL in `db-init/init-databases.sh` from the `sync_service` role onward - every statement there is safe to run against an already-initialized volume, since it's all `CREATE ROLE`/`GRANT`/`REVOKE`, nothing destructive to existing data).

## Verifying the sync/provider boundaries

```bash
# provider isolation (Phase 1)
docker compose exec postgres psql -U bkash_service -d nagad_db -c "SELECT 1;"
# -> permission denied for database "nagad_db"

# The aggregator/API path remains provider-scoped in the application layer
curl http://localhost:8000/metrics
# -> returns per-provider health plus validation metrics derived from the shared simulation state

# sync_service is read-only against provider DBs
docker compose exec postgres psql -U sync_service -d bkash_db -c "UPDATE balances SET emoney_balance = 0;"
# -> permission denied for table balances

# shared_service (aggregator-api's read-only credential) cannot write shared_db
docker compose exec postgres psql -U shared_service -d shared_db -c "CREATE TABLE probe (id int);"
# -> permission denied for schema public

# login works against aggregator-api's OWN database (aggregator_db)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=field.officer&password=Passw0rd!"
# -> 200, JWT access_token (see docs/CREDENTIALS.md for every seeded demo account)
```

Stop everything:
```bash
docker compose down          # keeps the postgres volume (pgdata)
docker compose down -v       # also wipes the postgres volume
```

## Environment variables

Defined in `backend/.env.example` — copy to `backend/.env` and adjust if
needed. Never commit `.env` with a real `OPENAI_API_KEY`.

| Variable | Purpose |
|---|---|
| `POSTGRES_SUPERUSER` / `POSTGRES_SUPERUSER_PASSWORD` | Used only by the `postgres` container itself and by `db-init/init-databases.sh` to create the 4 databases + roles. |
| `BKASH_DB_PASSWORD`, `NAGAD_DB_PASSWORD`, `ROCKET_DB_PASSWORD`, `SHARED_DB_PASSWORD`, `AGGREGATOR_DB_PASSWORD` | Passwords for the per-database restricted roles created at first startup. |
| `BKASH_DATABASE_URL`, `NAGAD_DATABASE_URL`, `ROCKET_DATABASE_URL`, `SHARED_DATABASE_URL`, `AGGREGATOR_DATABASE_URL` | Full connection strings each service uses. A service only ever receives the URL(s) it's allowed to use. |
| `SYNC_POLL_INTERVAL_SECONDS` | How often sync-service polls the provider databases (used from Phase 3). |
| `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Auth token signing (Phase 6). Dev-only default secret - override for any non-local deployment. |
| `DEMO_LOGIN_CODE` | Shared password for every seeded demo account (Phase 6) - see `docs/CREDENTIALS.md`. |
| `OPENAI_API_KEY` | Optional, not yet used (LLM helper is Phase 8, not built). Never make a live call without your explicit go-ahead, per your rules. |

## Startup sequence

1. `postgres` starts and runs `db-init/init-databases.sh` **only on first
   volume creation** — this creates `bkash_db`, `nagad_db`, `rocket_db`,
   `shared_db`, and one restricted-privilege role per database. If you change
   `db-init/init-databases.sh` later, it will **not** re-run against an
   existing volume — you'd need `docker compose down -v` first (destructive:
   wipes all Postgres data; I will ask before ever running this for you).
2. `provider-api`, `sync-service`, `aggregator-api` wait for `postgres`'s
   healthcheck (`pg_isready`) before starting.
3. Each service builds from its own `Dockerfile` + `requirements.txt` — no
   shared base image, no shared virtualenv.

## Troubleshooting

**"address already in use" on port 8000 / 5432 when running `docker compose up`**
Something else on your machine already owns that port. Two known causes in
this repo specifically:
- The **old single-process backend** (`cd backend && uvicorn app.main:app`)
  is still running and already bound to `:8000`. Stop it first, or don't run
  both stacks at once.
- A **system/other Postgres** already listening on `:5432`. This is why
  `docker-compose.yml` maps the container's 5432 to host port **5433**, not
  5432 — if you still hit a conflict, check `ss -tlnp | grep 5432` (or the
  port in question) before assuming it's this stack.

**`docker build` fails with a DNS/registry timeout pulling `python:3.12-slim` or `postgres:16-alpine`**
Usually transient. Retry `docker compose up --build`; if it persists, try
`docker pull python:3.12-slim` on its own to isolate whether it's Docker's
registry connectivity or something else.

**A provider role can connect to a database it shouldn't**
That's a real bug, not a config issue — re-run the boundary check:
```bash
docker compose exec postgres psql -U bkash_service -d nagad_db -c "SELECT 1;"
# must fail with: permission denied for database "nagad_db"
```

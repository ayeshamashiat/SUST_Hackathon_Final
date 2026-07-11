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
| `BKASH_DB_PASSWORD`, `NAGAD_DB_PASSWORD`, `ROCKET_DB_PASSWORD`, `SHARED_DB_PASSWORD` | Passwords for the per-database restricted roles created at first startup. |
| `BKASH_DATABASE_URL`, `NAGAD_DATABASE_URL`, `ROCKET_DATABASE_URL`, `SHARED_DATABASE_URL` | Full connection strings each service uses. A service only ever receives the URL(s) it's allowed to use. |
| `SYNC_POLL_INTERVAL_SECONDS` | How often sync-service polls the provider databases (used from Phase 3). |
| `OPENAI_API_KEY` | Optional. Leave blank to keep `aggregator-api`'s LLM helper in mock mode (added Phase 5). Never make a live call without your explicit go-ahead, per your rules. |

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

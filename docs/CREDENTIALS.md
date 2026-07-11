# Demo login credentials

Predetermined operations-hierarchy accounts, seeded automatically by
`backend/aggregator-api/app/auth/seed.py` (`seed_users`) against
aggregator-api's own database (`aggregator_db`). No self-registration
exists, and **customers never get a login** (Section 5 of the brief:
customers are a beneficiary of more reliable service, not a system user).

All accounts share the same demo password: **`Passw0rd!`** (override via the
`DEMO_LOGIN_CODE` env var before first startup - it only takes effect on the
first seed, since seeding is idempotent).

| Username | Role | Scope |
|---|---|---|
| `agent.agent-001` … `agent.agent-015` | Agent | That one outlet only (15 demo agents total - see `provider-api/app/seed_data.py` for the full list of names/areas) |
| `field.officer` | Field Officer | All agents/areas |
| `area.manager` | Area Manager | All agents/areas (read-only) |
| `ops.bkash` | Provider Operations | bKash only |
| `ops.nagad` | Provider Operations | Nagad only |
| `ops.rocket` | Provider Operations | Rocket only |
| `risk.compliance` | Risk & Compliance Analyst | All (read-only) |
| `management` | Management | All (read-only) |

## What each role can actually do right now

Enforced server-side in `aggregator-api/app/routers/aggregate.py` (not just
hidden in the UI) - a role-mismatched request gets a real `403`, not just a
missing button:

- **Agent**: can only query their own `agent_id` via `/aggregate/agent`,
  `/aggregate/forecast`, `/aggregate/anomaly` - a 403 on any other agent.
- **Provider Operations**: sees the shared (derived) cash figure for every
  agent, but only their own provider's balance/forecast/anomaly data -
  requesting another provider's data explicitly (`?provider=nagad` as a
  bKash ops login) 403s.
- **Field Officer / Area Manager / Risk & Compliance / Management**: full
  read access across all agents and providers.

**Not built yet**: alert routing, case ownership, acknowledge/escalate/
resolve actions. There is no `/alerts` or `/cases` endpoint in the current
backend - the frontend's "Anomaly Review" page shows the same detection
evidence directly instead of a case queue. This is the next phase of the
build (alert engine + case lifecycle), not a bug.

Log in at `/login` in the frontend, or via `POST /auth/login` (OAuth2
password form: `username`/`password`) against aggregator-api - the same
endpoint also powers the "Authorize" button in the FastAPI docs at
`http://localhost:8000/docs`.

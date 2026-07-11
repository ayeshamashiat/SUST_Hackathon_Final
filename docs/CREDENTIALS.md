# Demo login credentials

Predetermined operations-hierarchy accounts, seeded automatically by `backend/app/simulation/seed.py`
(`seed_users`). No self-registration exists, and **customers never get a login** (Section 5 of the
brief: customers are a beneficiary of more reliable service, not a system user).

All accounts share the same demo password: **`Passw0rd!`**

| Username | Role | Scope |
|---|---|---|
| `agent.zindabazar` | Agent | Zindabazar Bazar Corner only |
| `agent.shahjalal` | Agent | Shahjalal Uposhohor Outlet only |
| `agent.amberkhana` | Agent | Amberkhana Point only |
| `field.officer` | Field Officer | All agents/areas |
| `area.manager` | Area Manager | All agents/areas (read-only) |
| `ops.bkash` | Provider Operations | bKash only |
| `ops.nagad` | Provider Operations | Nagad only |
| `ops.rocket` | Provider Operations | Rocket only |
| `risk.compliance` | Risk & Compliance Analyst | All (read + case review) |
| `management` | Management | All (read-only) |

## What each role can do

- **Agent**: read-only view of their own outlet's cash + provider balances, forecast, and
  transactions. Cannot act on cases.
- **Provider Operations**: sees the shared cash figure plus only their own provider's balance/
  forecast for every agent - never another provider's numbers. Alerts/cases are filtered to their
  provider. Can acknowledge/escalate/resolve a case only if it's routed to "Provider Operations"
  for their own provider.
- **Field Officer**: full read access across agents/providers. Can act on cases routed to "Field
  Officer" (liquidity/cash cases).
- **Risk & Compliance Analyst**: full read access; can act on any case (review/escalation
  oversight). There is no "declare fraud" action anywhere in the system - alerts only ever say
  "unusual" or "requires review."
- **Area Manager** / **Management**: full read access across agents/providers/areas for
  situational awareness; view-only (no case mutation), matching that the current alert routing
  table doesn't assign case ownership to these roles yet.

Log in at `/login` in the frontend, or via `POST /auth/login` (OAuth2 password form:
`username`/`password`) against the backend - the same endpoint also powers the "Authorize" button
in the FastAPI docs at `/docs`.

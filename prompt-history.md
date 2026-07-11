# Prompt History

## Initial Solution Architecture Prompt

You are an experienced solution architect.

We are building a hackathon prototype for:

**bKash presents SUST CSE Carnival 2026**

The project is a safe decision-support system for a multi-provider mobile financial service "super agent" who serves customers through providers such as bKash, Nagad, and Rocket. The agent uses one shared physical cash drawer, but each provider has a separate e-money balance. The system should help the agent and provider teams understand liquidity pressure, provider imbalance, unusual transaction behavior, and who should coordinate the response.

The prototype must not:

- Claim fraud.
- Merge real wallets or imply provider-to-provider conversion.
- Execute financial actions.
- Connect to real production APIs, real wallets, customer accounts, OTPs, PINs, passwords, or credentials.
- Automatically block users, freeze funds, accuse agents, reverse transactions, or move liquidity.

The product should use simulated, anonymized, mock, or safe public data only.

### Core Problem

Many MFS agents serve multiple providers while using one pool of cash. A shop may look healthy if all balances are added together, but it can still fail operationally because:

- The shared cash drawer may run low.
- One provider's e-money balance may run low.
- Pressure may be concentrated in one provider.
- Transaction behavior may look unusual and require human review.
- The agent, field officer, provider operations team, and risk/compliance team may not know who should act first.

The system should make this situation easy to understand and should show evidence, uncertainty, responsible stakeholder, case owner, recommended next step, and resolution status for important alerts.

### Intended Users

- **Multi-provider agent**: needs one view of cash and each provider balance.
- **Provider operations / network coordination team**: monitors alerts, contacts agents, coordinates approved support, and tracks cases.
- **Risk or compliance analyst**: reviews unusual activity with evidence, but operations should not make a final fraud decision.
- **Financial service provider**: sees provider-specific service pressure while keeping data boundaries separate.
- **Management**: sees area-level service risk and readiness.
- **Customers**: benefit from more reliable service availability.

### Functional Expectations

Mandatory capabilities:

- Show shared physical cash and separate balances for each provider.
- Show which provider or shared cash reserve may face a shortage and approximately when.
- Detect at least one unusual activity pattern and show why it was flagged.
- Use careful language such as "unusual" or "requires review"; never declare fraud.
- For at least one important alert, show who receives it, who owns it, the recommended next step, and final status.
- Show lower confidence or a safe fallback when provider data is missing, late, or conflicting.
- Use AI, APIs, analytics, or data processing as a meaningful part of the product.

Recommended capabilities:

- Filter or prioritize by provider, agent, area, or time.
- Provide evidence and simple history for important alerts.
- Offer Bengali, Banglish, or English explanations.
- Show at least one simple Bengali or Banglish alert with situation, evidence, uncertainty, and safe next step.
- Support provider-specific escalation, case notes, alert history, and coordination while keeping provider boundaries clear.

Optional advanced capabilities:

- Cross-provider pattern insight or network relationships using simulated identifiers.
- What-if scenarios for provider demand, local events, or agent unavailability.
- Human review, case notes, feedback, and audit trails.
- Nearby-agent support discovery, alert assignment, acknowledgement, escalation timelines, resolution tracking, hotspot mapping, or graph-based relationship insight.

### Demonstration Scenarios

Scenario A - Hidden provider shortage:

A multi-provider agent appears healthy when all balances are added together, but one provider's e-money is about to run out. The prototype should show which provider is under pressure, when shortage may happen, confidence, and a safe next step.

Scenario B - Liquidity pressure with unusual activity:

The agent's physical cash is falling quickly and one provider shows a sudden rise in repeated or high-value transactions. The prototype should show both liquidity risk and the unusual pattern, explain that it may be normal Eid demand or may require review, and recommend human review before major action.

Scenario C - Cross-provider or data inconsistency:

Provider feeds arrive late or show conflicting balances. The prototype should warn about the data problem, reduce confidence, keep balances separate, and avoid misleading recommendations.

Scenario D - Coordinated response and closure:

A high-priority liquidity or anomaly alert affects one provider. The prototype should show who receives the alert, who owns it, recommended action, acknowledgement, and whether the issue was resolved or escalated.

### Required Deliverables

Judges should see:

- Working prototype with multi-provider balances, a liquidity or anomaly alert, and one coordinated/escalated case.
- Source repository with source code, README, setup steps, environment examples, and sample data.
- Architecture diagram showing interfaces, backend, data flow, analytics/AI services, monitoring, provider boundaries, and alert coordination flow.
- Data and simulation note explaining synthetic data, anomaly scenarios, assumptions, and limitations.
- Validation evidence with at least three measured metrics covering analytics, system performance, or reliability.
- Responsible-design note covering privacy, human review, false positives, advisory boundaries, and actions intentionally not performed.
- Final presentation covering problem, users, story-driven demo, architecture, metrics, coordination flow, risks, limitations, and next steps.

### Success Criteria

- Demonstrate meaningful multi-provider insight, not just separate charts on one screen.
- Connect liquidity and anomaly outputs in an explainable, safe decision-support flow.
- Important alerts must lead to a clear, traceable coordination path.
- Provider boundaries and integration limits must be respected.
- False positives, uncertainty, and data-quality failure modes must be acknowledged and tested.
- The prototype should present measurable analytical and system evidence end to end.

### Evaluation Focus

Judges will evaluate:

- Problem understanding and ecosystem relevance.
- Innovation and decision value.
- Technical implementation and integration quality.
- Data and analytical quality.
- User experience and explainability.
- Security, privacy, fairness, and responsible design.
- Presentation and demonstration quality.

### Implementation Request

Plan the whole completion of the project in **3 passes** and store the plan for later work as `initial_plan.md` in the repository.

Use:

- **Backend**: FastAPI.
- **Frontend**: Next.js.
- **Database**: preferably SQLite for prototype speed, with schemas designed for extension.
- **Analytics**: meaningful statistical/data-processing logic, not cosmetic AI.
- **Data**: synthetic provider/agent/transaction data only.

The plan should start with basic features, then recommended features, then advanced/polish features.

Also generate a simple explanation of the idea for knowledge transfer.

Highlight why the design is innovative, especially:

- It connects shared cash and separate provider balances.
- It uses provider-aware forecasting.
- It links liquidity pressure with unusual activity evidence.
- It routes alerts into human-owned coordination workflows.
- It keeps provider boundaries separate and safe.
- It shows uncertainty and degraded confidence when data quality is poor.

### Planned 3-Pass Delivery Structure

#### Pass 1 - MVP: Mandatory Rubric Rows

Goal: prove the full loop end-to-end:

unified view -> forecast -> one anomaly type -> one routed and owned alert -> careful language -> safe fallback.

Backend:

- Extend FastAPI skeleton.
- Add SQLModel + SQLite.
- Add models for Provider, Agent, CashDrawer, ProviderBalance, Transaction, DataFeedStatus, Alert, Case, and CaseEvent.
- Seed N agents x 3 providers with plausible opening state.
- Add background simulation loop for demo transactions.
- Implement Eid-rush scenario.
- Implement EWMA-style burn-rate forecaster for cash and provider balances.
- Implement one anomaly detector: rolling-window velocity spike using z-score.
- Add alert engine with evidence JSON and careful EN/BN templates.
- Add static routing table from alert type to stakeholder role.
- Auto-create case for each alert.
- Add PATCH endpoint for acknowledgement/status/resolution.
- Add DataFeedStatus and manual degrade-feed endpoint.
- Return `data_quality` and lower confidence when data is stale.
- Add REST endpoints for agents, balances, transactions, alerts, cases, simulation seed/reset/degrade.
- Configure CORS for local Next.js.

Frontend:

- Fresh Next.js app.
- `/` dashboard with selected agent, shared cash, 3 provider balances, time-to-shortage, confidence badge, and polling transaction ticker.
- `/alerts` page with severity, evidence summary, careful language, and case coordination details.
- Agent selector.
- Consistent provider color coding.

Deliverables:

- `initial_plan.md`
- `EXPLAINER.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_SIMULATION.md`
- README setup steps for both apps.
- Seed script.
- Pytest coverage for forecaster and detector.

Exit check:

- Every mandatory Section 7 row is demonstrable.
- First 7 rows of Section 16 checklist are demonstrable.

#### Pass 2 - Recommended Features + Measured Evidence

Goal: strengthen the product with richer review workflows, filtering, multilingual UX, and validation metrics.

Backend:

- Add more anomaly/data-quality detectors:
  - near-identical amount / small-account-group clustering,
  - balance reconciliation mismatch,
  - missing/late/conflicting feed scenarios.
- Improve confidence estimation with rolling variance or confidence interval logic.
- Add false-positive-risk documentation.
- Deepen case workflow with notes, audit history, and enforced escalation path.
- Add filters by provider, area, time, severity, and status.
- Add operations summary endpoint.
- Add live update channel if useful.
- Add evaluation harness measuring:
  - shortage detection lead time,
  - anomaly precision/recall,
  - false-positive rate,
  - explanation coverage,
  - API latency,
  - data-quality fallback behavior.

Frontend:

- Add EN/BN/Banglish toggle.
- Add operations view for multi-agent/area/provider prioritization.
- Add dedicated case detail page with notes and timeline.
- Add scenario controls for degraded feed/conflicting data.
- Add metrics page showing measured evidence.
- Add alert history and case notes.

Deliverables:

- `docs/VALIDATION.md`
- richer alert/case workflow
- documented metrics
- updated README/demo script

Exit check:

- Recommended Section 7 rows are demonstrable.
- At least three measured metrics are shown.
- Failure/uncertainty/false-positive behavior is documented.

#### Pass 3 - Optional Advanced Features + Demo Polish

Goal: make the solution feel innovative, complete, and presentation-ready.

Backend:

- Add cross-provider linkage detector using simulated customer identifiers.
- Add what-if scenario engine:
  - Eid-rush multiplier,
  - provider outage,
  - agent unavailable,
  - local event demand spike.
- Add nearby-agent advisory support suggestion based on area and surplus.
- Add human feedback loop:
  - normal demand,
  - requires review,
  - false positive,
  - escalated.
- Add hotspot aggregation by area/time/provider.
- Add performance profiling or load-test evidence.
- Add structured logging/observability where useful.

Frontend:

- Add scenario control panel for judges.
- Add cross-provider relationship/case view.
- Add area hotspot view.
- Add nearby-agent advisory support panel.
- Polish visual design, accessibility, and responsive behavior.
- Prepare final demo flow.

Final deliverables:

- Final architecture docs.
- Final data/simulation docs.
- Final validation docs.
- Responsible-design note.
- Presentation/demo notes.
- Optional demo video or review log.

Exit check:

- Full Section 16 checklist satisfied.
- Final presentation is ready

## Refactor Log

> Entries below follow the mandated Date / Prompt / Summary / Files format
> introduced when the permanent development rules (incremental phases,
> prompt logging, no unapproved destructive actions, etc.) were adopted.
> Earlier sections above are the original planning document and are left
> untouched.

### 2026-07-11 — Refactor to Docker Compose / provider-separated architecture

**Prompt**: Refactor the existing single-process FastAPI + SQLite backend
(built across the sessions logged above) into a simpler multi-service
architecture: one Postgres container with four databases (`bkash_db`,
`nagad_db`, `rocket_db`, `shared_db`); one `provider-api` FastAPI app with
`/bkash`, `/nagad`, `/rocket`, `/simulator` routers, each router touching only
its own database; one `sync-service` that polls providers and populates
`shared_db` as a read-only projection; one `aggregator-api` that reads only
`shared_db` and hosts the alert engine, forecast engine, anomaly detector, and
a new `services/llm.py` OpenAI abstraction (mock + live mode) as internal
modules, not separate services. Explicit instruction to inspect the current
codebase first, explain what exists/changes/can be reused/should be removed,
and wait for confirmation before writing any code; work one phase at a time.

**Summary**: Inspected the entire existing backend (models, analytics,
alerts, cases, simulation, API routers, tests) and reported back: almost all
business logic (`forecaster.py`, `anomaly.py`, `alerts/engine.py`,
`routing.py`, `templates.py`, `cases/workflow.py`, the `agents`/`alerts`/
`cases` routers) can move into `aggregator-api` unchanged, just repointed at
Postgres. Flagged three open design gaps the instructions didn't resolve:
who owns the shared `CashDrawer` (not provider data — no provider DB is a
natural home for it), whether `sync-service` polls providers over HTTP or
connects to their databases directly, and how the frontend (single origin,
port 8000 today) stays compatible once the backend splits into three
services. No code changed in this turn — pure inspection and a proposed
6-phase plan (infra → move modules → sync-service → rewire aggregator →
LLM abstraction → full verification + docs), logged as tracked tasks.

**Files modified**: None (analysis only).

---

### 2026-07-11 — Resolve open design questions, begin Phase 1

**Prompt**: Use the hackathon problem statement as the source of truth to
decide who owns `CashDrawer`; make the pragmatic call on the other two open
questions rather than re-asking; keep the result frontend-compatible.

**Summary**: Re-read the problem statement's framing of physical cash
("agent has one physical cash drawer," never described as provider-visible
data) and concluded `CashDrawer` is agent-reported ground truth that was
never meant to flow through the provider-sync pipeline — it lives in
`shared_db` but is the one table there written directly by `provider-api`'s
`/simulator` router, not by `sync-service`. Settled the other two gaps:
`sync-service` connects directly to each provider Postgres database with its
own restricted credentials (no HTTP hop through `provider-api`); `aggregator-
api` stays the only host-exposed service (port 8000, matching the frontend's
existing `NEXT_PUBLIC_API_BASE_URL` default), with `/simulation/*` becoming
an internal proxy to `provider-api`'s `/simulator` router so the frontend
needs zero changes. Built and verified Phase 1 (infra only, no business logic
moved yet): `docker-compose.yml` (postgres + provider-api + sync-service +
aggregator-api), `db-init/init-databases.sh` (creates the 4 databases + one
restricted role per database), `.env.example`, and health-check-only FastAPI
skeletons for the three new services. Verified end-to-end: all containers
built and reported healthy, every `/health` endpoint responded, and the
provider-boundary guarantee was proven directly against Postgres — the
`bkash_service` role gets `permission denied for database "nagad_db"` when
it tries to connect to Nagad's database, and `shared_service` likewise cannot
reach `bkash_db`. Verification ran on a temporary alternate port (8010)
because the pre-existing single-process backend was still running and bound
to 8000; the compose file was reverted to the intended `8000:8000` mapping
afterward and the verification stack was torn down. The old
`backend/app/`, `sust_hackathon.db`, and `venv/` were not touched. Added
`docs/deployment.md` documenting the new Docker workflow, env vars, startup
sequence, and troubleshooting (including the port-8000-conflict situation
just hit).

**Files modified**:
- `backend/docker-compose.yml` (new)
- `backend/.env.example` (new)
- `backend/db-init/init-databases.sh` (new)
- `backend/provider-api/{Dockerfile,requirements.txt,app/main.py,app/__init__.py}` (new)
- `backend/sync-service/{Dockerfile,requirements.txt,app/main.py,app/__init__.py}` (new)
- `backend/aggregator-api/{Dockerfile,requirements.txt,app/main.py,app/__init__.py}` (new)
- `docs/deployment.md` (new)

---

### 2026-07-11 — Phase 2: Provider API balance/transaction endpoints + seed script

**Prompt**: Implement the provider layer completely: identical
`/provider/balance/{agent_id}`, `/provider/transactions`, `/provider/health`
endpoints for bkash/nagad/rocket, each provider isolated to its own
database; a seed script generating ~10-20 super agents registered across all
three providers with realistic, non-corrupting-on-rerun synthetic
transactions; reuse code across providers instead of triplicating CRUD;
`is_injected_anomaly` must never reach a customer-facing response. Backend
only, no architecture changes, stop and wait for approval after this phase.

**Summary**: Added `app/models.py` (`Balance`, `Transaction` - one shared
SQLModel schema applied to three independent engines), `app/db.py` (three
fully separate engine/session pairs, one per provider, no shared session),
`app/services.py` (provider-agnostic query functions - isolation comes from
which `Session` a router hands in, not from anything in the service layer),
and `app/routers/factory.py` (`build_provider_router(provider, get_db)`,
called once per provider so the three routers share one implementation
while each closes over its own DB dependency). Added `app/seed_data.py` (15
Sylhet-area demo agent identities, reused later when aggregator-api seeds
its own `Agent` table) and `app/seed.py` (idempotent per-provider seeding -
generates a chronologically-ordered transaction ledger per agent and derives
the opening `emoney_balance` from it, so seeded data is internally
consistent with the same cash/e-money coupling the analytics layer expects).
Wired both into `main.py`'s startup lifecycle. Verified end-to-end against
`postgres` + `provider-api` only (left `sync-service`/`aggregator-api` and
the still-running old SQLite backend untouched): confirmed all endpoints
work, balances differ per provider for the same agent, `is_injected_anomaly`
never appears in a transaction response, an unseeded agent 404s, a missing
`agent_id` query param 422s, restarting the container does not duplicate or
reset seeded data, and - re-confirming Phase 1's guarantee still holds now
that real tables exist - `bkash_service`'s Postgres role still cannot even
connect to `nagad_db`.

**Assumptions made**: (1) The literal endpoint paths in the brief
(`/provider/balance/{agent_id}` etc.) are mounted under each provider's
existing `/bkash` `/nagad` `/rocket` prefix, giving e.g.
`/bkash/provider/balance/{agent_id}` - not a bare top-level path, since three
providers can't share one unprefixed path. (2) No reset/clear endpoint was
requested for Phase 2 seed data (only "works repeatedly without corrupting
data," satisfied by the idempotent skip-if-already-seeded check) - a
reset control, if wanted, reads as a Phase 3 simulator concern. (3) Balance
`last_updated` is set to "now" at seed time (representing "confirmed as of
this snapshot") rather than pinned to the single most recent transaction's
timestamp.

**Files modified** (all new, under `backend/provider-api/app/`):
- `models.py`, `db.py`, `config.py`, `schemas.py`, `services.py`
- `seed_data.py`, `seed.py`
- `routers/factory.py`, `routers/bkash.py`, `routers/nagad.py`, `routers/rocket.py`
- `main.py` (rewritten: startup lifespan now calls `init_db()` + `seed_all()`, includes the three provider routers)

---

### 2026-07-11 — Phase 3: Transaction simulator

**Prompt**: Implement the transaction simulator as part of Provider API
(not a separate container) with four modes - normal, Eid demand spike
(legitimate, must not resemble suspicious activity), injected anomaly
(near-identical amounts, repeated accounts, tight window, tagged
`is_injected_anomaly=True`, never exposed publicly), and feed delay (pause
one provider's updates so sync confidence is affected later) - behind
exactly four endpoints: `POST /simulator/run`, `POST /simulator/inject-anomaly`,
`POST /simulator/feed-delay`, `GET /simulator/status`. No architecture
changes, stop after this phase.

**Summary**: Added `app/simulator/` to provider-api: `state.py` (in-memory,
single-process - a restart resets pause flags/active scenario, not the
transaction data itself, which lives in Postgres), `engine.py`
(`apply_transaction` - the same cash/e-money coupling `seed.py` uses, so live
generation stays consistent with seeded history - plus `generate_normal`,
`generate_eid_spike`, `generate_anomaly_burst`, and the background `tick()`
loop), and `schemas.py`. Added `app/routers/simulator.py` exposing the four
requested endpoints, with input validation against the known provider/agent
lists (400, not a silent no-op, on an unknown value). Wired a background
tick loop into `main.py`'s lifespan (starts automatically, like the old
single-process app's simulator did) so there's continuous live movement for
a demo by default, on top of which the four endpoints let you inject a
specific scenario on demand. `/simulator/run`'s `duration_minutes` lets an
Eid spike persist across many ticks rather than being a single flat batch.
Feed delay is implemented as a genuine pause (the paused provider's
`balances.last_updated` simply stops advancing) rather than artificially
backdating anything - Phase 4's sync-service will derive staleness from that
frozen timestamp naturally.

Verified end-to-end against `postgres` + `provider-api` only (old backend
and the other two new services untouched): background loop generates
normal-mode transactions immediately on startup; `/simulator/run` with
`mode=eid_spike` produced diverse, wide-ranging account references and
mostly cash-out transactions - visibly not anomaly-shaped; `/simulator/
inject-anomaly` produced a tight cluster of near-identical (~5000 BDT ±30)
cash-outs from a 3-account repeating pool, correctly interleaved with
ambient normal traffic in the transaction history; `/simulator/feed-delay`
froze rocket's transaction count and `last_updated` timestamp while bkash/
nagad kept advancing during the same two tick cycles, then resumed cleanly;
unknown provider/agent values on any endpoint return 400; `is_injected_
anomaly` confirmed absent from every transaction response via direct grep.

**Assumptions made**: (1) A background tick loop runs by default (matching
the old app's behavior and the original brief's "not just real-time
background generation" phrasing, which implies background generation is the
baseline the on-demand endpoints supplement). (2) `/simulator/run` triggers
an immediate batch synchronously and, if `duration_minutes > 0`, also sets
the ambient mode for the background loop going forward - not two unrelated
behaviors. (3) No explicit stop-the-whole-loop endpoint was requested, so
none was added; `feed-delay` only pauses one provider at a time, by design.

**Files modified** (all new, under `backend/provider-api/app/`):
- `simulator/state.py`, `simulator/engine.py`, `simulator/schemas.py`
- `routers/simulator.py`
- `main.py` (starts/stops the background loop in `lifespan`, includes the simulator router)

---

### 2026-07-11 — Phase 4: Sync service

**Prompt**: Implement synchronization from the three provider databases into
`shared_db` (a read-only projection - only the Sync Service may write to it).
Poll `bkash_db`/`nagad_db`/`rocket_db`, populate `provider_balances` and
`transactions_projection`, compute `staleness_seconds` and `sync_status`
(`ok`/`delayed`/`failed`/`conflicting`) per provider per agent. Sync must be
idempotent (no duplicate projected transactions), maintain `synced_at`
timestamps, and the stored staleness/status must be positioned to actually
drive forecast confidence later (Phase 5), not just sit there unused. Stop
after this phase; include a suggested commit message.

**Summary**: Added `sync-service/app/`: `provider_models.py` (a deliberate,
read-only duplicate of provider-api's `Balance`/`Transaction` schema - the
two services are independently deployable, so they share a DB contract, not
Python code), `models.py` (shared_db's actual schema: `ProviderBalance`
upserted per agent+provider, append-only `TransactionProjection`, and
`SyncState` - a per-provider watermark/failure-tracking table), `sync.py`
(the real workflow), and a background loop in `main.py` wired the same way
as provider-api's simulator loop.

`sync_status` is a severity-ranked, genuinely-triggered state machine, not a
name attached to a guess: **failed** when the poll itself raises (caught,
doesn't crash the cycle - existing projection rows are kept and just
re-flagged, never blanked); **conflicting** when a provider's own polled
balance doesn't reconcile with its own transaction history since the last
successful sync (`existing_balance + new_transaction_deltas` vs. the
provider's actual current balance, outside a float-rounding epsilon) -
self-clears once the mismatch source stops recurring, rather than being a
permanent quarantine; **delayed** when `source_updated_at` (the provider's
own `balances.last_updated`, not sync-service's clock) hasn't advanced past
`SYNC_STALE_AFTER_SECONDS`; **ok** otherwise. This is exactly what makes
Phase 3's feed-delay simulator meaningful end-to-end: pausing a provider
there really does turn into `delayed` here.

Idempotency: a per-provider `last_synced_txn_id` watermark makes each poll
incremental (only fetch transactions past the watermark), plus an
existence check against `transactions_projection` before inserting (defends
against re-processing the same batch if a crash landed between insert and
watermark-commit) and a DB-level unique constraint on `(provider,
provider_txn_id)` as a schema-level backstop.

**Also corrected the DB permission model** (this phase's "only the Sync
Service may write to shared_db" requirement forced the issue): `db-init/
init-databases.sh` now creates a `sync_service` role with read-only grants
on the three provider databases (via `ALTER DEFAULT PRIVILEGES FOR ROLE
<provider>_service`, so it also covers any table created after this script
runs) and full read-write on `shared_db` (it owns/creates that schema).
`shared_service` (unused until now - reserved for aggregator-api, Phase 5)
had its grants corrected from the original "ALL PRIVILEGES" down to
`SELECT`-only, via `ALTER DEFAULT PRIVILEGES FOR ROLE sync_service ... TO
shared_service`. Since the actual Postgres volume from Phases 1-3 already
existed (and `db-init` only runs on a database's first initialization), the
equivalent grants were also applied live against the running container, non-
destructively - no data was wiped. Caught and fixed one mistake during that
live correction: the first `REVOKE ALL PRIVILEGES ON SCHEMA public FROM
shared_service` ran against the wrong database (missing `-d shared_db`,
so it silently hit the default `postgres` maintenance DB instead) - verified
this by testing that `shared_service` really couldn't create a table
afterward, caught that it still could, traced it to the missing `-d` flag,
and fixed it before moving on.

**Verified end-to-end** against `postgres` + `provider-api` + `sync-service`
(old backend and aggregator-api untouched): all 45 agent×provider balances
projected correctly; a Phase-3 anomaly burst's 9 transactions survived
projection with `is_injected_anomaly=true` intact; re-ran a full cycle and
restarted the container mid-stream - zero duplicate `(provider,
provider_txn_id)` pairs either time; used `/simulator/feed-delay` to pause
bkash and confirmed all 15 of its projected rows genuinely went `delayed`
after `SYNC_STALE_AFTER_SECONDS` elapsed, then recovered to `ok` after
resuming; revoked and restored `sync_service`'s `CONNECT` on `bkash_db`
(terminating its pooled connection first, since a revoke doesn't kill an
already-open session) and confirmed all 15 rows genuinely went `failed`
with `consecutive_failures` incrementing, then recovered; directly tampered
with a balance via `UPDATE balances SET emoney_balance = emoney_balance +
99999` (bypassing its own transaction ledger) and confirmed the very next
cycle flagged it `conflicting`, then confirmed it self-cleared to `ok` once
the mismatch source stopped recurring. Re-confirmed Phase 1's provider
boundary still holds, and additionally confirmed `sync_service` cannot
write to any provider DB and `shared_service` cannot write to `shared_db`.

**Files modified**:
- `backend/sync-service/app/provider_models.py`, `models.py`, `config.py`, `db.py`, `sync.py` (all new)
- `backend/sync-service/app/main.py` (rewritten: background sync loop + `/sync/status`)
- `backend/db-init/init-databases.sh` (adds `sync_service` role, corrects `shared_service` to read-only)
- `backend/.env.example`, `backend/docker-compose.yml` (new `SYNC_*` credentials/URLs)
- `docs/deployment.md` (documents the 5-role permission model and how to apply it to a pre-Phase-4 volume)

---

### 2026-07-11 — Phase 5: Aggregator API

**Prompt**: Implement aggregator-api's analytics endpoints, reading only
`shared_db` (never provider databases): `GET /aggregate/agent/{agent_id}`
(cash balance, all provider balances, staleness, confidence) and
`GET /aggregate/forecast/{agent_id}` (burn rate, projected shortage,
confidence depending on staleness/missing/conflicting providers), plus
explainable rule-based anomaly detection (rolling z-score, frequency
analysis, account clustering - no black-box model; evidence must cite
transaction IDs/timestamps/amounts; careful language only - "unusual",
"requires review", "low confidence", never "fraud"). Don't modify
provider-api. Stop after this phase; show a recommended commit message.

**Summary**: A real gap surfaced immediately: `GET /aggregate/agent/{id}`
is required to return a cash balance, but no component in this rebuilt
architecture has ever generated, stored, or synced one - Phase 3's simulator
only ever writes provider e-money transactions, and Phase 4 made `shared_db`
writable by sync-service alone. Resolved it the way already established for
this exact tension back in Phase 0 (cash isn't provider data, so it was
never going to arrive via provider sync) but adapted to this phase's
tighter, explicit constraint ("read ONLY shared_db"): rather than having any
service write a cash column, `services/cash.py` **derives** the cash balance
read-only, from `transactions_projection` already sitting in `shared_db` -
every `cash_out` decreases cash (agent hands over physical money) and every
`cash_in` increases it, the same coupling already established in
provider-api's models/seed/simulator. A single documented opening-balance
constant (`CASH_OPENING_BALANCE = 80,000`) stands in for a real per-agent
starting-cash source, which does not exist yet - called out explicitly in
`config.py` as a modeling assumption, not a hidden guess. No writes anywhere,
no provider-api change, satisfies "read only shared_db" exactly as stated.

Ported the burn-rate forecaster and velocity-anomaly detector's statistical
approach from the earlier single-service prototype (proven, already
documented there) onto `shared_db`'s schema, and added the confidence
wiring the brief explicitly requires: `services/confidence.py` turns
Phase 4's `staleness_seconds`/`sync_status` into a `HIGH`/`MEDIUM`/`LOW`
signal (missing provider row, `failed`, and `conflicting` all map to `LOW`;
`delayed` or staleness past 60s maps to `LOW`; otherwise `MEDIUM`/`HIGH` by
freshness), and every forecast/aggregate response takes the *weaker* of its
own statistical confidence and this data-quality confidence - a
clean-looking trend computed from stale or conflicting source data cannot
report as `HIGH`. Cash's confidence is the weakest across all three
providers, since it depends on all of them.

The anomaly detector combines three signals rather than z-score alone,
specifically because a naive frequency-only detector would flag Phase 3's
legitimate Eid-spike traffic as unusual (it IS high-volume): a rolling
z-score of window transaction count vs. this agent+provider's own recent
baseline (frequency), and an account-concentration ratio (unique accounts /
window count) (clustering) - both must deviate together before anything is
flagged, plus an amount-coefficient-of-variation figure carried as
supporting evidence. Evidence cites real `provider_txn_id`s, timestamps, and
amounts pulled directly from `transactions_projection`; every message uses
"unusual"/"requires review"/confidence language and explicitly states "this
is not a fraud determination."

Added a third endpoint, `GET /aggregate/anomaly/{agent_id}`, not named in
the brief's literal endpoint list - added so the detector has a
demonstrable, sampleable output of its own (per this phase's "sample
output" deliverable); Phase 6's alert engine is what will turn a flagged
result here into a routed, owned Alert/Case.

**Also fixed a real isolation gap found during verification**: every
service was using `env_file: .env`, which hands EVERY service's credentials
to EVERY container - `aggregator-api` was receiving `nagad_service`'s full
read-write password in its own environment despite never reading it in
code, meaning "aggregator must never query provider databases" was only
true because the code didn't currently try, not because it couldn't.
Replaced `env_file: .env` with an explicit `environment:` allow-list per
service in `docker-compose.yml` (provider-api gets only its 3 provider
URLs; sync-service gets only its `SYNC_*` credentials; aggregator-api gets
only `SHARED_DATABASE_URL` + the shared staleness threshold) - `.env` is
still the single source of values via Compose's `${VAR}` substitution, it's
just no longer injected wholesale into every container. Verified by reading
each container's actual environment directly.

**Verified end-to-end** against all four services (old backend untouched),
reusing the demo data accumulated across Phases 2-4 in the persisted
Postgres volume: `/aggregate/agent` correctly showed per-provider
confidence dropping to `LOW` for a genuinely stale provider and `MEDIUM`
for fresh-but-not-instant ones; `/aggregate/forecast` showed `AT_RISK` cash
with `top_contributors` correctly attributing most of the drain to bkash,
and confidence correctly downgraded by the same staleness; triggered a
fresh anomaly burst via Phase 3's simulator on a clean agent and confirmed
`/aggregate/anomaly` flagged it live with real transaction-id evidence;
triggered a fresh Eid-spike batch and confirmed it was **not** flagged
despite a high z-score (2.79), because its account-concentration ratio was
1.0 (fully diverse) - the exact false-positive this detector's two-signal
design exists to avoid; re-confirmed the DB-level provider/shared_db
boundaries still hold and additionally confirmed via `docker compose exec
... env` that aggregator-api's container carries no provider-database
credential at all after the compose fix.

**Files added** (`backend/aggregator-api/app/`): `config.py`, `db.py`,
`models.py`, `schemas.py`, `services/confidence.py`, `services/cash.py`,
`services/forecast.py`, `services/anomaly.py`, `routers/aggregate.py`;
`main.py` updated to include the new router.
**Files modified**: `backend/docker-compose.yml` (env allow-lists),
`docs/deployment.md` (documents the env-scoping fix).

---

### 2026-07-11 — SonarQube + CI/CD pipeline

**Prompt**: Analyze every commit with SonarQube; run SonarQube in Docker,
wired into a CI/CD pipeline.

**Summary**: Explained CI/CD and SonarQube in beginner terms first, per the
standing rules, then surfaced the one real architectural constraint before
building anything: GitHub Actions runs on temporary cloud machines with no
network path to a Docker container on this laptop, so "SonarQube in Docker"
and "analyzed on every commit via CI" can't be the same running instance.
Asked the user to choose between SonarCloud (hosted, persistent dashboard,
needs a free external signup), an ephemeral Docker-in-CI scan (self
contained, no persistent history), or local-only (no CI yet). User chose
**SonarCloud**.

Built: `sonarqube/docker-compose.yml` (local, persistent SonarQube +
its own Postgres, for scanning on-demand from this machine - independent of
CI, satisfies the literal "Docker" requirement); `sonar-project.properties`
at repo root (shared by both the local scanner and CI, with placeholder
`sonar.projectKey`/`sonar.organization` the user must replace with their
real SonarCloud project's values); `.github/workflows/sonarcloud.yml`
(triggers on every push and PR, uses the official `SonarSource/
sonarqube-scan-action`, authenticates via a `SONAR_TOKEN` GitHub secret);
`docs/sonarqube.md` (explains the two-target split, local usage, the
one-time SonarCloud account/token/secret setup the user has to do
themselves since it requires their own external credentials, what the CI
workflow does step by step, and troubleshooting).

Verified: both `sonarqube/docker-compose.yml` and `.github/workflows/
sonarcloud.yml` parse as valid YAML/compose config. Confirmed the host's
`vm.max_map_count` (1048576) is already well above SonarQube's Elasticsearch
minimum (262144), so no host-level sysctl change was needed. **Could not
fully verify the local SonarQube container live**: the `sonarqube:community`
image pull ran unusually slowly in this environment (confirmed via network
byte-delta sampling that it was genuinely transferring, not stalled) and had
not finished after roughly 25 minutes; left it running in the background
rather than continuing to block on it. CI cannot be verified at all without
the user completing the SonarCloud signup + `SONAR_TOKEN` secret step
themselves (external account, not something achievable from this session).

**Files added**: `sonarqube/docker-compose.yml`, `sonar-project.properties`,
`.github/workflows/sonarcloud.yml`, `docs/sonarqube.md`.


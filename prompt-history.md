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

---

### 2026-07-11 — Discovered a backend fork; ported auth/RBAC to the new architecture

**Prompt**: "Make the current frontend consistent with the current backend," followed shortly by "I can't login, it shows 404."

**Summary**: Started rewiring the existing 2-page frontend to aggregator-api's
real endpoints (new `lib/types.ts`/`api.ts`/`agents.ts`, reworked `Badges`/
`BalanceCard`, an honest "Anomaly Review" page replacing the non-functional
"Alerts & Cases" page). Mid-rewrite, file-state reminders showed my own
edits being silently reverted, and `git log` revealed why: **61 files had
landed on `main` via a merged PR that this session had zero visibility
into** - a complete, separate build-out of auth/RBAC, an alert engine, an
LLM helper, offline evaluation, and `/metrics`, all on top of `backend/app/`
(the old single-service SQLite backend), plus a full RBAC frontend (login,
role-scoped UI) built against *that* backend. Both backends bind to port
8000 and are mutually exclusive - the 404 was literally just my Docker
stack occupying the port instead of the auth-capable old backend.

Immediately unblocked the user (stopped my stack, installed the old
backend's new deps, ran it, verified `POST /auth/login` worked), then
surfaced the fork explicitly rather than silently picking a side - asked
which backend should be "the" one going forward. **User chose the new
multi-service architecture** (real Postgres-enforced provider isolation,
idempotent sync, the historical-baseline anomaly detector) over the old
one (further along on features, but the provider "isolation" is just a
column filter in one SQLite file). Framed the remaining work as five
ordered phases (6: auth, 7: alert engine, 8: LLM, 9: evaluation/metrics,
10: frontend), explicit that the old backend's new code is the *reference
to port from*, not wasted effort.

**Phase 6 (this session)**: Auth needs somewhere to write (users, later
alerts/cases), but `shared_db` is sync-service's exclusive write domain by
design (Phase 4). Rather than carve an exception into that rule, gave
aggregator-api its own database - `aggregator_db`, owned by a new
`aggregator_service` role - so aggregator-api writes its own domain data to
a database it actually owns, and the "only sync-service writes shared_db"
guarantee never needs an exception. Ported `security.py` (password hashing,
JWT), `deps.py` (`get_current_user`, `require_roles`), the `User`/`UserRole`
model, and the `/auth/login` + `/auth/me` routes from the old backend
essentially unchanged (same libraries: passlib, PyJWT). Also applied the
old backend's per-request scope-checking pattern to the *existing*
`/aggregate/*` endpoints (Phases 1-5 work) rather than leaving them merely
"logged-in-gated": `AGENT` logins 403 on any agent but their own,
`PROVIDER_OPS` logins 403 on any provider but their own (cash stays visible
cross-provider to every role, matching the old backend's own precedent -
it's the agent's own asset, not provider-confidential data).

Then finished what the login page needs to actually be useful: merged the
already-solid RBAC frontend auth machinery (`AuthProvider`, `AuthGate`,
`authStorage`, the login page, `UserBadge` - all reused untouched) with the
real aggregator-api data layer built earlier this session, replacing the
old-backend-shaped `lib/api.ts`/`types.ts` calls. Dashboard now shows real
cash/provider balances + forecasts; "Anomaly Review" shows both detectors'
live evidence with an explicit banner stating case ownership/escalation
isn't built yet (Phase 7), rather than shipping dead buttons.

**Verified end-to-end**: login → JWT → `/auth/me` all correct; unauthenticated
`/aggregate/*` calls now 401; `agent.agent-001` login 403s on `agent-002`,
200s on its own agent; `ops.bkash` login sees only `bkash` in the provider
list and 403s when explicitly requesting `?provider=nagad`; full frontend
typecheck and lint clean; all four backend containers healthy, sync caught
up with zero failures. Updated `docs/CREDENTIALS.md` (was listing the old
backend's 3-agent usernames and case-actions that don't exist here yet) and
`docs/deployment.md` (new 6th Postgres role, new env vars) to match reality.

**Files added**: `backend/aggregator-api/app/auth/{__init__.py,models.py,
security.py,deps.py,seed.py}`, `backend/aggregator-api/app/routers/auth.py`,
`frontend/src/components/AnomalyCard.tsx`, `frontend/src/lib/agents.ts`.
**Files modified**: `backend/db-init/init-databases.sh` (+aggregator_db/
aggregator_service), `backend/.env.example`, `backend/docker-compose.yml`
(new env vars for all 3 app services), `backend/aggregator-api/app/{config.py,
db.py,schemas.py,main.py,routers/aggregate.py}`, `backend/aggregator-api/
requirements.txt` (passlib, PyJWT, python-multipart), `frontend/src/{lib/
api.ts,lib/types.ts,app/page.tsx,app/alerts/page.tsx,app/layout.tsx,
components/Badges.tsx,components/BalanceCard.tsx}`, `docs/CREDENTIALS.md`,
`docs/deployment.md`.
**Files removed**: `frontend/src/components/AlertCard.tsx`,
`frontend/src/lib/caseTransitions.ts` (case-lifecycle UI with nothing to
call yet - will be rebuilt properly in Phase 7).

---

### 2026-07-11 — Bulk historical data + per-agent historical anomaly baseline

**Prompt**: Need a huge amount of historical data across all databases, and
the data should be able to tell whether a given transaction type is
suspicious for a *specific* agent, based on that agent's own history. Asked
where to generate it from.

**Summary**: Explained the real gap first: historical data has to originate
in the provider databases (never `shared_db`/aggregator-api, which are
read-only projections), and separately, simply having more history in the
database wouldn't make detection any smarter - the existing anomaly detector
(Phase 5) only ever looks at a 60-minute rolling window, so "is this unusual
for this agent's history" needed a genuinely new, additive detector, not
just more data.

Built `provider-api/app/historical_seed.py` - an on-demand (not automatic-
on-startup) bulk generator with realistic weekday/weekend and time-of-day
shaping (Bangladesh Fri/Sat weekend runs busier; volume weighted toward
business hours, not uniform-random). Idempotent per agent+provider: only
backfills the gap older than the requested window, and extends the existing
running balance by the prequel's own net effect rather than recomputing
from scratch, so it never duplicates or corrupts data already seeded by the
quick-seed or live simulator. Ran it for 90 days: ~146,000 transactions
created across the three provider databases (48,907 / 49,137 / 47,834).

Added `services/anomaly.detect_amount_outlier` in aggregator-api - a new,
separate detector from the existing velocity/clustering one: evaluates an
agent's single most recent transaction against that specific agent's own
historical mean/stdev (default 30-day lookback, minimum 20 prior samples
before trusting the statistic), flagging when it's a statistical outlier
for *that agent specifically* - not a fleet-wide or generic amount
threshold. Exposed as a new endpoint, `GET /aggregate/anomaly/{agent_id}
/historical`. Same careful-language rule as the existing detector: "unusual
for this agent," "should be reviewed," "not a fraud determination."

**Found and fixed a real reliability bug while verifying at this volume**:
syncing the ~146k-row backlog, sync-service's background loop died silently
- an exception during a large sync cycle (most likely a stale pooled
connection from when `docker compose up --build` had incidentally recreated
the postgres container) propagated out of `sync_all()` uncaught, permanently
ending the asyncio loop with nothing printed to the logs to explain why.
Confirmed the underlying sync logic itself was fine (running `sync_provider`
manually completed correctly, just took time for a 45k-row batch) - the bug
was purely in error handling. Fixed at two layers: `sync_all()` now catches
per-provider so one provider's failure doesn't skip the others in the same
cycle, and `main.py`'s `_loop()` now catches per-cycle so a single bad cycle
can never end the background task, logging the exception instead of
swallowing it silently. Applied the identical fix to provider-api's
simulator loop as the same class of risk, proactively, before it caused the
same silent failure there.

**Verified end-to-end**: confirmed the "not enough data" path correctly
declines to judge before backfilling; ran the 90-day backfill; watched
sync-service correctly catch up all three providers with zero failures
after the fix (previously stuck indefinitely on two of three providers);
queried a real agent's historical baseline (719 prior transactions, mean
2,643 BDT); injected one 45,000 BDT transaction for that same agent and
confirmed it was flagged HIGH confidence with z=31.0 against their own
history, citing the specific transaction id and their real historical
average; confirmed response latency stayed well under 250ms across all
`/aggregate/*` endpoints at the new ~146k-row data volume.

**Documented limitation**: the outlier detector uses a simple mean/stdev,
so one injected outlier inflates its own future baseline's standard
deviation once enough time passes for it to enter the historical window -
a median/MAD-based approach would be more robust to this but wasn't built
given time constraints; noted here rather than silently left unstated.

**Files added**: `backend/provider-api/app/historical_seed.py`.
**Files modified**: `backend/aggregator-api/app/config.py` (new tuning
constants), `backend/aggregator-api/app/services/anomaly.py`
(`detect_amount_outlier` + `AmountOutlierResult`), `backend/aggregator-api/
app/schemas.py` (`AmountOutlierOut`), `backend/aggregator-api/app/routers/
aggregate.py` (new `/aggregate/anomaly/{agent_id}/historical` endpoint),
`backend/sync-service/app/main.py` + `sync.py` (background-loop reliability
fix), `backend/provider-api/app/main.py` + `simulator/engine.py` (same fix
applied proactively).

---

### 2026-07-11 — Phase 7: alert assignment + case-lifecycle workflow (backend + frontend)

**Prompt**: First asked for a top-to-bottom stakeholder assignment/escalation
loop across the brief's roles (Agent, Operations Team, Risk/Compliance,
Management, Providers), in both frontend and backend. Mid-implementation
(before any case/alert code was written - only a shared-constants refactor
had landed), interrupted with a much more specific, self-contained spec:
severity/type-based assignment rules (High liquidity → Provider Ops, Medium
→ Field Officer, Suspicious pattern → Risk Analyst, Data missing →
Technical Support, Low → Agent only), an explicit 8-state alert lifecycle
(NEW → ASSIGNED → ACKNOWLEDGED → UNDER_REVIEW → {RESOLVED, MONITORING,
ESCALATED} → ... → CLOSED), required fields (Alert, Case Notes, Assignment
History), and hard constraints (never fraud declarations, never financial
actions, never merge provider balances).

**Summary**: Reconciled the new spec against what already existed before
writing code. Two real conflicts surfaced and were confirmed with the user
via AskUserQuestion rather than guessed: (1) the spec's "Technical Support"
target for data-quality alerts isn't one of the 6 already-seeded login
roles - resolved by mapping it to Provider Ops (they already own their
provider's feed health) rather than adding a 7th role/account; (2) the
spec's 5-stakeholder list omits Area Manager, which already exists as a
seeded RBAC role from the earlier phase - resolved by keeping the login
functional but dropping it from the automatic assignment ladder (dashboard-
only for now).

Built one escalation ladder (not per-category chains):
`AGENT → FIELD_OFFICER → PROVIDER_OPS → RISK_COMPLIANCE → MANAGEMENT`.
Alert type + severity only decide the entry point (`cases/routing.py`'s
`ASSIGNMENT_RULES`, evaluated top-down, documented as the place to edit
policy); escalating always just moves to the next rung, reassigning
ownership and resetting to `UNDER_REVIEW`.

Data model deliberately merged into two tables instead of four: `Alert`
(with `current_owner`/`current_status` embedded directly, per the spec's
Required Fields) and one append-only `CaseEvent` audit table whose rows
serve as case notes (`NOTE_ADDED`), assignment history (`ASSIGNED`/
`ESCALATED`/`REASSIGNED`), and the full audit trail (every row) via three
filtered views in `AlertOut` - not three separate never-delete tables.
Bilingual (EN/BN/Banglish) narratives are built directly from the existing
forecast/anomaly evidence numbers (`cases/narratives.py`), no LLM call
(Phase 8 not built yet). Data-quality alerts reuse sync-service's own
`sync_status` (`ok`/`delayed`/`failed`/`conflicting`) rather than
duplicating feed-health tracking. The alert-evaluation loop follows the
exact same pattern as sync-service's background loop (per-cycle exception
catch, since that was a real bug found and fixed earlier this session).

**Verified end-to-end against the live Docker stack** (rebuilt and
restarted `aggregator-api` only): confirmed alerts are created and assigned
automatically by the background loop; walked one real alert through the
entire lifecycle via curl with real role logins - `ops.bkash` acknowledged
→ started review → escalated with a reason → reassigned to
`risk.compliance` → resolved → closed, with the audit trail showing every
step in order; confirmed RBAC works both ways (403 when `field.officer`
tries to act on a Provider-Ops-owned case, 403 when `ops.nagad` reads a
bKash-owned alert, 400 when trying to act on an already-`CLOSED` case).

**Frontend**: added `AlertOut`/`CaseEventOut` types and
acknowledge/start-review/note/monitor/resolve/escalate/close calls to
`lib/api.ts`; added `AlertCaseCard` (bilingual message toggle, evidence,
recommended action, role-gated action buttons, full audit trail) and new
badge components; replaced the Anomaly Review page's "not implemented yet"
banner with a live "Coordination - assigned cases" section (open/mine/
closed filters) sitting above the existing raw detection-evidence section.
**Could not verify visually in a browser this session** - the Chrome
extension wasn't connected, and Next.js's single-instance-per-directory
lock meant a second dev server couldn't be started for the preview tools to
attach to either. Verified instead via a clean `tsc --noEmit`, a clean
`next lint` (only pre-existing, unrelated error in `auth.tsx`), and watching
the already-running dev server recompile the changed files with no errors
across several edits. Recommended the user click through it manually or
that this be re-verified in a session with a working Chrome connection.

**Files added**: `backend/aggregator-api/app/agents.py`,
`backend/aggregator-api/app/cases/{__init__,models,routing,narratives,
engine,workflow}.py`, `backend/aggregator-api/app/routers/alerts.py`,
`frontend/src/components/AlertCaseCard.tsx`.
**Files modified**: `backend/aggregator-api/app/auth/seed.py` (import
shared constants instead of duplicating), `backend/aggregator-api/app/
{config,db,main,schemas}.py`, `frontend/src/lib/{types,api}.ts`,
`frontend/src/components/Badges.tsx`, `frontend/src/app/alerts/page.tsx`.

---

### 2026-07-12 — Stakeholder-specific dashboards (Phase 1 of a much larger enterprise-UX ask)

**Prompt**: Restated the Field Officer / Provider Operations / Risk-
Compliance / Management responsibility lists and asked that the stakeholder
dashboards contain all of them, then attached a very large "enterprise-
grade decision-support dashboard" spec (ServiceNow/PagerDuty/Sentinel-style
UI; an AI Summary panel on every page; explainable risk-contribution score
breakdowns; historical baseline comparison; a non-destructive what-if
simulator; nearby-outlet discovery; area heatmaps; recurring-pattern
detection; similar-historical-case lookup; resolution analytics; and five
fully-featured, role-specific dashboards).

**Summary**: This is a full product redesign, not an incremental change -
today there was one generic dashboard page shared by every role. Rather
than attempt the entire spec at once, proposed a 7-phase breakdown (role
dashboards → explainability layer → timeline/resolution analytics →
what-if simulation → historical comparison/pattern detection → area
intelligence/nearby-outlet/similar-case search → enterprise visual pass)
and asked the user to confirm scope before writing code. Confirmed: Phase 1
only (stakeholder dashboards) for this turn.

Built five role-specific dashboard routes, all reusing data that already
existed (no new backend endpoints this phase - resolution-time/escalation-
count/resolution-rate metrics are computed client-side in the new
`lib/caseMetrics.ts` from each alert's own `audit_trail`, which already
carries every timestamp needed):

- `/agent` - the existing balance-card view, plus a "Your cases" section
  (backend already scopes an AGENT login's `/alerts` to their own agent).
- `/field-officer` - KPI row, an "assigned agents" priority-ranked table
  (grouped client-side by `agent_id`), and their own verification queue via
  the existing `AlertCaseCard`.
- `/operations` - the most feature-rich, per the brief: live incident
  queue, an escalation-activity table (both directions - escalated by them
  or reassigned to them), and resolution-time KPIs, all provider-scoped by
  the backend automatically.
- `/risk` - anomaly/data-quality-focused review queue (liquidity cases
  optionally included), reinforcing "requires human review" language
  rather than any fraud label.
- `/management` - executive KPIs, an area-performance table (joined
  client-side against `lib/agents.ts`'s existing per-agent `area` field, no
  backend change needed), a provider-comparison table, and a simple
  alert-volume-by-day view. Read-only by design per the brief ("Management
  should not manage individual incidents") - the only actionable list is
  cases that actually reached Management at the top of the escalation
  ladder.

`/` now redirects each role to its dashboard instead of showing one
generic view; the top nav is now role-aware (`NavLinks.tsx`, a new small
client component - `layout.tsx` itself stays a server component). Also
deduplicated `ROLE_LABEL` (was hand-copied in `UserBadge.tsx`; now imported
from `Badges.tsx`, which already had an identical copy from last phase).

**Verified**: clean `tsc --noEmit`; clean `next lint` (only the same
pre-existing, unrelated `auth.tsx` error from before, not something this
turn touched); fixed two React Compiler "could not preserve memoization"
errors it caught in `field-officer` and `management` (a `useMemo` depending
on a freshly-filtered array literal each render, rather than the actual
`alerts` state - removed the unnecessary `useMemo` in both spots since the
lists involved are small); confirmed all 7 routes (`/`, `/agent`,
`/field-officer`, `/operations`, `/risk`, `/management`, `/alerts`) return
200 with zero new server-side errors logged, by curling each directly
against the user's already-running dev server. Same as last phase, could
not do a real visual/click-through check - Chrome extension unavailable,
and Next.js's single-instance-per-directory lock blocks a second dev server
for the preview tools to attach to.

**Files added**: `frontend/src/components/{KpiCard,NavLinks}.tsx`,
`frontend/src/lib/caseMetrics.ts`, `frontend/src/app/{agent,field-officer,
operations,risk,management}/page.tsx`.
**Files modified**: `frontend/src/app/page.tsx` (now a role-based
redirect), `frontend/src/app/layout.tsx` (nav extracted to `NavLinks`),
`frontend/src/components/UserBadge.tsx` (dedupe `ROLE_LABEL`),
`frontend/src/lib/api.ts` (`getAlerts` gained a `limit` param, default
raised to 300 for fleet-wide dashboards).

---

### 2026-07-12 — Phase 2: explainability layer (AI summary, risk breakdown, ranked recommendations)

**Prompt**: "do phase 2" - confirming the second item from the 7-phase
enterprise-dashboard breakdown proposed last turn.

**Summary**: Built three rule-based explainability pieces and wired them
into the existing `AlertCaseCard` (used by all 5 dashboards) plus a
page-level summary panel on every dashboard:

- **Risk-contribution breakdown** (`lib/riskContribution.ts`) - decomposes
  each alert's `evidence` (already returned by the backend) into named
  factors with point weights (e.g. "Rapid cash-out activity vs. baseline
  +32", "Concentrated in a small group of accounts +24"), summed into a
  0-100 score. Explicitly documented and labeled in the UI as hand-authored
  explainability weights, not a trained model's feature importance -
  deliberately not presented as calibrated statistics.
- **Ranked recommendation engine** (`lib/recommendations.ts`) - expands the
  backend's single `recommended_action` into an ordered action list per
  (alert type, current owner), so the same liquidity case shows different
  ranked actions depending on whether Field Officer, Provider Ops, or
  Management currently owns it. Scores are labeled "priority", not
  "confidence" - a ranking weight for ordering, not a probability claim.
- **AI Summary panel** (`lib/aiSummary.ts` + `components/AiSummaryPanel.tsx`)
  - a fixed-template paragraph per dashboard summarizing open-case count,
  severity, dominant alert type/provider, and the single most urgent case.
  Deliberately template-based, not a live LLM call (Phase 8/`services/
  llm.py` isn't built yet, and this project's standing rule is mock-mode-
  by-default without an explicit go-ahead) - every instance carries a
  visible "not a live model call" caption so it's never mistaken for a real
  generative summary. Considered including a "similar past patterns"
  sentence like the brief's own example, but Phase 5 (historical
  comparison) doesn't exist yet, so left it out rather than assert
  something unverifiable.

Also added a distinct "Confidence reduced" callout in `AlertCaseCard` when
an alert's confidence is LOW, surfacing the existing `confidence_note` as a
labeled reason rather than leaving it blended into the evidence footer.

**A judgment call worth flagging**: the spec's own example showed numeric
confidence percentages ("93%", "42%"). Deliberately did NOT fabricate
those - the backend only ever computes a genuine 3-level HIGH/MEDIUM/LOW
confidence (see `services/confidence.py` from an earlier phase), and
inventing a fake decimal-precision percentage from that would be less
honest, not more, given the brief's own "never hide uncertainty" /
responsible-AI framing. Kept the qualitative badge and reason text instead
of adding false precision.

**Verified**: clean `tsc --noEmit`, clean `next lint` (same pre-existing,
unrelated `auth.tsx` error as prior phases), all 7 routes still return 200
with zero new server errors after the change (checked by curling the
user's already-running dev server directly). Same browser-verification gap
as the last two phases - no Chrome connection available this session.

**Files added**: `frontend/src/lib/{riskContribution,recommendations,
aiSummary}.ts`, `frontend/src/components/{AiSummaryPanel,
RiskContributionBar,RecommendationList}.tsx`.
**Files modified**: `frontend/src/components/AlertCaseCard.tsx` (wired in
risk breakdown, ranked recommendations, confidence-reduced callout),
`frontend/src/app/{agent,field-officer,operations,risk,management,
alerts}/page.tsx` (AI Summary panel added to each).


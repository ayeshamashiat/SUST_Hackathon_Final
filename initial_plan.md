# bKash SUST CSE Carnival 2026 — Multi-Provider Liquidity & Coordination Prototype

> This is the living project plan. It is written once at the start and updated at the end of each pass with what actually shipped vs. what moved. Read this first before starting work on any pass.

## Context

This is a hackathon prototype for the brief: a decision-support tool for a multi-provider ("super agent") MFS outlet serving bKash, Nagad, and Rocket customers out of one physical cash drawer and three separate e-money balances. It must give a unified liquidity view, forecast shortages, flag unusual activity with evidence (never "fraud"), and route important alerts to the right human through an ownership/escalation/resolution workflow — without ever touching real wallets or making a final decision.

The build is broken into **3 incremental passes** (basic → recommended → advanced/polish), mirroring the challenge brief's own Mandatory / Recommended / Optional tiers (Section 7), so each pass is a self-contained, demoable submission. Backend = FastAPI. Frontend = Next.js. Narrative/alert text generation is **fully offline, template-based** (no external LLM API calls) — analytics/detection satisfies the "use AI/analytics" requirement through statistical/rule-based methods (EWMA forecasting, z-score anomaly detection), not a black box.

See [`EXPLAINER.md`](EXPLAINER.md) for a plain-language walkthrough of the idea, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the system diagram.

## Why this design is innovative

1. **Cross-provider correlation only a super-agent view can see.** A single provider's ops team only sees their own leg of a transaction. Our cross-provider detector (Pass 3) links a synthetic customer fingerprint doing near-identical cash-outs across *two different providers* at the *same agent* within minutes — a pattern invisible to any one provider alone. This is the concrete answer to "why does a unified view matter beyond convenience."
2. **Cash and e-money modeled as a coupled system, not independent gauges.** The forecaster understands that cash-out drains cash *and* fills e-money, and cash-in does the reverse — so it can explain *why* an imbalance is emerging (e.g., "heavy one-directional cash-out demand"), not just plot three unrelated lines.
3. **Evidence-first, uncertainty-visible alerting.** Every alert is a structured object — metric, threshold, contributing transactions, confidence — never a black-box score. Confidence visibly degrades when a provider feed is stale/missing/conflicting (Scenario C), which is testable, not just claimed.
4. **A routing graph, not a flat alert list.** Alerts follow the real escalation hierarchy (agent → field officer → area manager → provider ops → risk/compliance) with acknowledge/own/resolve states, turning "an alert fired" into "a tracked case with a paper trail" — directly what objective 4 and the mandatory coordination row ask for.
5. **Offline-safe, template-based narration with graceful degradation as a feature, not a compromise.** Because narration is templated (no external API), the "safe fallback under bad/missing data" requirement and the "no live-demo network risk" goal reinforce each other — the same code path that produces confident English text produces "data delayed, confidence lowered" text.
6. **The 3-pass structure mirrors the brief's own Mandatory/Recommended/Optional tiers** (Section 7), so progress maps directly onto the judging rubric (Section 13) rather than being an arbitrary engineering split.

## Domain model (core entities)

- `Provider` — bKash / Nagad / Rocket (simulated, logically separate; id, display name, color).
- `Agent` — the outlet (id, name, area/thana).
- `CashDrawer` — one shared physical-cash balance per agent.
- `ProviderBalance` — one e-money balance per (agent, provider).
- `Transaction` — `CASH_IN` or `CASH_OUT`, agent, provider, amount, synthetic customer id, timestamp, area, status. Cash-out: `cash -= amount`, `provider_balance += amount`. Cash-in: reverse.
- `DataFeedStatus` — per (agent, provider): last update time, staleness/conflict flag — drives the safe-fallback behavior.
- `Alert` — type (liquidity / anomaly / data-quality), severity, agent, provider(s), evidence (JSON of contributing transactions + metric values), confidence, EN/BN/Banglish message.
- `Case` — alert_id, routed stakeholder role, owner, status (`NEW → ACKNOWLEDGED → IN_PROGRESS → ESCALATED → RESOLVED`), recommended next step.
- `CaseEvent` — audit trail entries (created, acknowledged, note added, escalated, resolved) for traceability.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI + Uvicorn (extends existing `backend/app` skeleton) | Already scaffolded; async-friendly for WS/live simulation. |
| DB | SQLite via SQLModel (SQLAlchemy + Pydantic) | Zero-infra, file-based, trivial to reset/reseed for a demo; documented as the swap-to-Postgres path for "production." |
| Simulation | asyncio background task + scenario presets | Drives a "live" Eid-rush feel without external data. |
| Realtime | FastAPI native WebSocket (`/ws/live`), Pass 2+ | Live ticker/alerts instead of polling for the demo. |
| Frontend | Next.js (App Router) + TypeScript + Tailwind | Replaces the current Vite/React scaffold. |
| Charts | Recharts | Gauges + timeseries for balances/forecasts. |
| Tests | pytest (backend), type-check + manual golden-path (frontend) | Detector/forecaster correctness, alert/case state machine. |

## Repository layout (target)

```
backend/app/
  core/        # config, db session
  models/      # SQLModel tables
  schemas/     # Pydantic I/O
  simulation/  # seed data + scenario engine
  analytics/   # forecaster + anomaly detectors
  alerts/      # alert engine + routing table
  cases/       # case/audit-trail workflow
  narrative/   # EN/BN/Banglish templates
  api/         # routers + websocket
  tests/
frontend/        # fresh Next.js app (App Router)
  app/(dashboard)/, alerts/, cases/[id]/, operations/, scenarios/, metrics/
  components/, lib/ (api client, ws hook, i18n dicts)
docs/
  ARCHITECTURE.md, DATA_SIMULATION.md, VALIDATION.md, RESPONSIBLE_DESIGN.md
initial_plan.md   # this plan, persisted for later passes
EXPLAINER.md      # simple-terms knowledge-transfer doc
```

---

## Pass 1 — MVP: the Mandatory rubric rows

**Goal:** prove the full loop end-to-end — unified view → forecast → one anomaly type → one routed & owned alert → careful language → safe fallback — with schemas designed for extension later, not throwaway code.

Backend:
- Extend existing FastAPI skeleton; add SQLModel + SQLite; models listed above.
- Seed script: N agents × 3 providers with a plausible opening state.
- Simulation: background asyncio loop appending transactions for a demo agent (configurable rate), implementing an "Eid rush" pattern (Scenario A).
- Analytics: EWMA burn-rate forecaster (cash + each provider balance) projecting time-to-threshold with a coarse High/Medium/Low confidence bucket; one anomaly detector — rolling-window velocity spike (z-score vs baseline) matching Scenario B's "too many cash-outs in a short window."
- Alert engine: thresholds → `Alert` rows with evidence JSON + EN/BN careful-language templates ("may run out," "unusual," "requires review" — never "fraud").
- Static routing table (alert type → stakeholder role); each alert auto-creates a `Case` (status `NEW`, routed owner); `PATCH` endpoint to acknowledge/change status/resolve.
- `DataFeedStatus` + a manual "degrade feed" endpoint; forecaster demotes confidence and API returns a `data_quality` flag when a feed is stale — no confident number is shown on bad data.
- REST endpoints: agents, balances, transactions, alerts (+basic filters), alert case get/patch, simulation seed/reset/degrade.
- CORS updated for `localhost:3000`.

Frontend (fresh Next.js app):
- `/` dashboard: cash gauge + 3 provider balance bars for a selected agent, time-to-shortage readout with confidence badge, polling-based transaction ticker.
- `/alerts`: list with severity, evidence summary, careful language, click-through to case (owner, status, next step) — satisfies the mandatory coordination row.
- Agent selector; consistent provider color coding.

Deliverables produced this pass: `initial_plan.md`, `EXPLAINER.md`, `docs/ARCHITECTURE.md` v1, `docs/DATA_SIMULATION.md` v1, README setup steps for both apps, seed script, pytest for forecaster + detector.

**Exit check:** every "Mandatory" row in Section 7 and the first 7 rows of the Section 16 checklist are demonstrable end-to-end.

---

## Pass 2 — Recommended features + measured evidence

Backend:
- Two more anomaly detectors: near-identical-amount/small-account-group clustering (Scenario B); balance-reconciliation mismatch (opening + Σtx ≠ feed value → flagged as *data problem*, not review-worthy — demonstrates the "distinguish demand spike vs data problem vs pattern requiring review" objective).
- Confidence upgraded to real stats (rolling-window variance-based CI); detectors emit a documented false-positive-risk figure.
- Case workflow deepened: `CaseEvent` audit trail, enforced escalation path (Field Officer → Area Manager → Provider Ops → Risk/Compliance for anomalies), case notes endpoint.
- Filtering: provider/area/time-range/severity query params; `area` added to `Agent`/`Transaction`; `/operations/summary` aggregation for management/provider-ops views.
- Data-quality simulation controls (late feed / conflicting balance / missing field) to demo Scenario C live.
- `/ws/live` WebSocket replacing polling for transactions/alerts/case updates.
- Evaluation harness: inject known synthetic anomalies, compute precision/recall; instrument API latency (p50/p95) middleware; log behavior under degraded feed — feeds `docs/VALIDATION.md`.

Frontend:
- EN/BN/Banglish toggle wired to backend templates (matching the brief's illustrative Bangla wording style).
- `/operations`: multi-agent/area grid for Provider Ops & Management.
- `/cases/[id]`: ownership, escalation timeline (stepper), notes thread, resolve/escalate actions.
- `/scenarios` (data-quality tab): live feed-degradation buttons, watch confidence/badges react.
- `/metrics`: the ≥3 measured metrics from the evaluation harness.
- WS-driven live ticker + alert toasts.

**Exit check:** Section 7 "Recommended" rows + ≥3 measured metrics + Section 16 checklist through case history/routing rows.

---

## Pass 3 — Optional/advanced + demo polish

Backend:
- Cross-provider linkage detector (the headline innovation); "possible cross-provider structuring, requires review," explicitly only detectable via the unified view.
- What-if scenario engine (Eid-rush multiplier / agent-unavailable / provider-outage presets) via `/scenarios/run` for a live judge-triggered story.
- Nearby-agent advisory support suggestions (area + surplus based) — clearly advisory, creates a coordination case, never moves funds.
- Human feedback loop: accept/reject/"normal Eid demand" action on alerts feeding the false-positive tracking on `/metrics` over time.
- Area/time hotspot aggregation; load/latency profiling script + `docs/PERFORMANCE.md`; structured logging around detectors/feed ingestion.

Frontend:
- Cross-provider case view highlighting linked transactions across provider columns.
- Finished scenario control panel narrating Scenarios A–D end-to-end for the live demo.
- Nearby-agent support suggestion panel; simple area heat grid.
- Final careful-language/accessibility/responsive pass.

Deliverables (final): all Section 10 items complete — working prototype, source repo, `docs/ARCHITECTURE.md` final, `docs/DATA_SIMULATION.md` final, `docs/VALIDATION.md` final (≥3 metrics), `docs/RESPONSIBLE_DESIGN.md`, presentation/demo notes.

**Exit check:** full Section 16 submission checklist satisfied.

---

## Verification approach (each pass)

- Backend: `pytest` covering forecaster math, each detector against hand-built fixtures (known-positive and known-negative cases), alert routing table, case state-machine transitions.
- API smoke test: run `uvicorn`, hit `/health`, seed data, walk one scenario via curl/HTTPie to confirm alert → case creation.
- Frontend: `npm run build` (type-check) + manually exercise the golden path in-browser (dashboard loads live data, an alert appears, clicking through shows a routed/owned case, language toggle switches text, degrading a feed visibly lowers confidence) per each pass's new pages before calling it done.
- Evaluation harness (Pass 2+) is itself the validation-evidence deliverable — rerun and re-record numbers at the end of Pass 2 and Pass 3.

## Progress log

- **Pass 1**: shipped MVP loop end-to-end — FastAPI + SQLModel/SQLite models, startup seed/reset/seed/degrade simulation controls, background Eid-rush transaction generator, EWMA-style liquidity forecaster, velocity-spike anomaly detector, careful-language alert templates, static routing, case ownership/status workflow, stale-feed confidence downgrade, REST endpoints, CORS for local Next.js, dashboard, alerts/cases page, setup READMEs, `docs/DATA_SIMULATION.md`, and pytest coverage for forecaster/anomaly/routing/cases. Verified with `python -m pytest app/tests` and `npm run build`.
- **Pass 2**: _pending._
- **Pass 3**: _pending._

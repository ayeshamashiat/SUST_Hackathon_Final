# Architecture

> v1 — written at the start of Pass 1. Update this diagram and the component notes at the end of each pass as pieces land.

## System diagram

```mermaid
flowchart TB
    subgraph SIM["Simulation Engine (backend)"]
        SEED["Seed script<br/>agents x providers, opening balances"]
        TICK["Scenario-driven transaction generator<br/>(asyncio background loop)"]
        DEGRADE["Feed-degradation controls<br/>(stale / conflicting / missing)"]
    end

    subgraph DB["SQLite (SQLModel)"]
        T_AGENT["Agent"]
        T_CASH["CashDrawer"]
        T_BAL["ProviderBalance"]
        T_TX["Transaction"]
        T_FEED["DataFeedStatus"]
        T_ALERT["Alert"]
        T_CASE["Case / CaseEvent"]
    end

    subgraph ANALYTICS["Analytics (backend)"]
        FORECAST["Liquidity Forecaster<br/>EWMA burn-rate + confidence"]
        DETECT["Anomaly Detectors<br/>velocity spike / near-identical amounts /<br/>balance reconciliation / cross-provider linkage"]
    end

    subgraph ALERTS["Alert & Coordination Engine (backend)"]
        ENGINE["Alert Engine<br/>thresholds -> Alert + evidence + confidence"]
        ROUTE["Routing table<br/>alert type -> stakeholder role"]
        CASEWF["Case workflow<br/>NEW -> ACK -> IN_PROGRESS -> ESCALATED -> RESOLVED"]
        NARR["Narrative templates<br/>EN / BN / Banglish, careful language"]
    end

    subgraph API["FastAPI"]
        REST["REST routers<br/>/agents /balances /transactions<br/>/alerts /cases /metrics /simulation"]
        WS["WebSocket /ws/live<br/>(Pass 2+)"]
    end

    subgraph FE["Next.js frontend"]
        DASH["/ dashboard<br/>cash + 3 provider gauges, forecast"]
        AL["/alerts<br/>evidence, severity, careful language"]
        CS["/cases/[id]<br/>owner, escalation timeline, notes"]
        OPS["/operations<br/>multi-agent / area view"]
        SC["/scenarios<br/>what-if + data-quality controls"]
        MET["/metrics<br/>precision/recall, latency, lead time"]
    end

    SEED --> DB
    TICK --> T_TX
    DEGRADE --> T_FEED
    T_TX --> FORECAST
    T_TX --> DETECT
    T_FEED --> FORECAST
    T_FEED --> DETECT
    FORECAST --> ENGINE
    DETECT --> ENGINE
    ENGINE --> ROUTE --> T_ALERT
    ROUTE --> CASEWF --> T_CASE
    ENGINE --> NARR
    T_ALERT --> REST
    T_CASE --> REST
    REST --> DASH
    REST --> AL
    REST --> CS
    REST --> OPS
    REST --> SC
    REST --> MET
    WS -.-> DASH
    WS -.-> AL
```

## Component notes

- **Provider boundary**: `ProviderBalance` rows are keyed by `(agent_id, provider_id)` and are never summed into a single "combined wallet" value in storage — only displayed side by side. No code path converts or transfers value between providers.
- **Validation & metrics**: the `/metrics` endpoint reports proxy metrics for sync latency, forecast lead time, anomaly precision/recall, alert explanation coverage, and per-provider sync health so the demo can show operational evidence without pretending to be a production observability stack.
- **Simulation Engine**: the only source of transactions/balances (no real provider APIs are called, per challenge constraints). Scenario presets (A–D from the brief) are parameter sets fed into the same generator, not special-cased code paths — this keeps the demo and the "real" logic identical.
- **Analytics**: pure functions over `Transaction`/`ProviderBalance`/`DataFeedStatus` history — deterministic, unit-testable, no external calls. This is what satisfies the "use AI/analytics meaningfully" requirement without any LLM dependency.
- **Alert & Coordination Engine**: the only place that writes `Alert`/`Case`/`CaseEvent` rows. Routing table is a static, documented mapping (alert type → stakeholder role) — explicit and auditable rather than implicit.
- **Narrative templates**: parameterized strings per alert type/language, filled with evidence values computed upstream — templates never invent evidence, they only phrase it.
- **API layer**: stateless REST + a WebSocket fan-out (added Pass 2) for live updates; all endpoints read from the same DB the analytics/alert engines write to, so the frontend never talks to the simulation directly.
- **Frontend**: role-oriented pages (agent dashboard, ops/coordination views) rather than one generic table — matches the brief's distinct stakeholder needs (Section 5).
- **Auth**: backed by a `User` table (`backend/app/models/models.py`) and JWT bearer tokens (`backend/app/core/security.py`, `backend/app/core/deps.py`), issued via `POST /auth/login`. Accounts are predetermined/seeded only (`backend/app/simulation/seed.py`) — no self-registration and no customer login, per Section 5. Every API route (except `/`, `/health`, `/auth/login`) requires a valid token, and each role's data/case-mutation access is scoped server-side (see `docs/CREDENTIALS.md` for the account list and per-role rules).

## Provider boundary & real-world integration limits

This prototype represents bKash/Nagad/Rocket as three logically separate simulated systems sharing one physical cash observation point. It does not integrate with, authenticate against, or move value through any real provider API. "Unified view" means *read-side aggregation for display and analytics only* — never a merged balance, shared ledger, or cross-provider settlement. This boundary is enforced at the data model level (separate `ProviderBalance` rows, no cross-provider transfer operation exists in the codebase) and is called out explicitly in `docs/RESPONSIBLE_DESIGN.md` (added Pass 2).

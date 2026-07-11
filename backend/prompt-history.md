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


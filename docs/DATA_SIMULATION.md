# Data Simulation

This prototype uses fully synthetic data. It does not ingest real bKash, Nagad, Rocket, agent, customer, wallet, or settlement data.

## Seed Data

On backend startup, `app.main` initializes SQLite and seeds demo rows if no agents exist. `POST /simulation/seed` is an idempotent manual seed endpoint, and `POST /simulation/reset` clears the demo tables and reseeds a clean run.

Seeded entities:

- Providers: bKash, Nagad, Rocket, each with a display color.
- Agents: demo outlets with area labels.
- Cash drawer: one shared physical-cash balance per agent.
- Provider balances: one separate e-money balance per agent/provider pair.
- Feed status: one freshness row per agent/provider pair.

The provider balances are intentionally not merged. A unified view can display all balances side by side, but the app keeps each provider ledger separate.

## Transaction Rules

Every generated transaction is either `CASH_OUT` or `CASH_IN`.

- `CASH_OUT`: the shared cash drawer decreases and that provider's e-money balance increases.
- `CASH_IN`: the shared cash drawer increases and that provider's e-money balance decreases.

If the outlet does not have enough cash for a cash-out, or enough provider e-money for a cash-in, the simulated transaction is recorded as `FAILED` and no balance is changed. Failed transactions are shown in the ticker but excluded from forecasting and anomaly baselines.

## Scenario A: Eid Rush Liquidity Pressure

The background simulator runs every few seconds and uses agent profiles to create heavier cash-out demand than normal. This drives a visible drop in the shared cash reserve and gives the EWMA-style forecaster enough recent data to project a time-to-threshold.

The forecast output includes:

- target balance (`CASH` or a provider id),
- current balance,
- burn rate per minute,
- projected shortage time,
- confidence bucket,
- confidence note,
- top provider contributors for cash pressure.

The API and UI use careful wording such as "may run out" and "requires review" rather than treating a forecast as a final decision.

## Scenario B: Velocity Spike

Some agent profiles occasionally inject a burst of cash-outs for one provider. The velocity detector compares the current rolling window against the same agent/provider's recent baseline. It emits evidence such as window count, baseline mean, standard deviation, z-score, unique customer count, amount range, and sample transaction ids.

The alert language intentionally says "unusual activity" and "requires review"; it never says "fraud."

## Scenario C: Degraded Feed

`POST /simulation/degrade-feed` freezes one provider feed. The simulator stops refreshing that feed's `last_update_at`, the alert engine marks it stale, and data-quality alerts are generated. Forecasts that depend on stale data are downgraded to low confidence and include a caveat.

Example request:

```bash
curl -X POST http://localhost:8000/simulation/degrade-feed ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_id\":\"agent-01\",\"provider_id\":\"bkash\",\"degrade\":true}"
```

Set `degrade` to `false` to restore the heartbeat.

## Reproducibility

The simulator uses randomized transaction amounts, customers, and provider choices, so each run is slightly different. For a clean demo, call:

```bash
curl -X POST http://localhost:8000/simulation/reset
```

Then open the dashboard and alerts page while the backend is running. The simulator will continue appending synthetic transactions in the background.

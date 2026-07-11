# SUST Hackathon Final Prototype

Decision-support prototype for a multi-provider MFS super-agent outlet. The app simulates one shared cash drawer serving bKash, Nagad, and Rocket balances, forecasts shortages, flags unusual activity with evidence, and routes alerts into human-owned cases.

## Run The Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API starts on `http://localhost:8000`, creates `sust_hackathon.db` if needed, seeds the demo data on startup, and starts the background simulator.

Useful endpoints:

- `GET /health`
- `GET /agents`
- `GET /agents/{agent_id}/balances`
- `GET /agents/{agent_id}/forecast`
- `GET /aggregate/forecast`
- `GET /agents/{agent_id}/transactions`
- `GET /alerts`
- `POST /alerts/{id}/acknowledge`, `POST /alerts/{id}/escalate`, `POST /alerts/{id}/resolve`
- `GET /cases/{case_id}` and `PATCH /cases/{case_id}`
- `GET /metrics`
- `POST /simulation/seed`, `POST /simulation/reset`, `POST /simulation/degrade-feed`
- `POST /simulate/scenario`

Run backend tests:

```bash
cd backend
python -m pytest app/tests
```

## Run The Frontend

```bash
cd frontend
npm install
npm run dev
```

The Next.js app runs on `http://localhost:3000` and expects the backend at `http://localhost:8000`. To point it elsewhere, create `frontend/.env.local` with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Build check:

```bash
cd frontend
npm run build
```

## Demo Flow

1. Open the dashboard and select a demo agent.
2. Watch the shared cash reserve, provider balances, shortage forecasts, and recent transactions update by polling the API.
3. Open Alerts & Cases to review liquidity, anomaly, or data-quality alerts.
4. Expand an alert to inspect evidence, confidence, routing owner, recommended next step, and case history.
5. Use case actions to acknowledge, start work, escalate, or resolve the advisory case.
6. Trigger safe fallback with `POST /simulation/degrade-feed` and confirm the UI/API show delayed feed status and low-confidence data quality.

All balances and transactions are simulated. The app never connects to real wallets and never labels a customer or transaction as fraud.

## Assumptions And Validation Notes

- Each provider is treated as a logically isolated ledger keyed by `(agent_id, provider_id)`; the prototype does not support cross-provider transfers or shared settlement.
- The metrics endpoint reports operational proxies rather than production-grade SLA telemetry; values are derived from the local simulation state and should be interpreted as demo evidence.
- Provider isolation is enforced by the data model and router-level filters, and the regression tests cover that boundary for bKash, Nagad, and Rocket.

# Backend

FastAPI backend for the multi-provider liquidity and coordination prototype.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The service runs at `http://localhost:8000`. On startup it initializes SQLite, seeds demo data if needed, and starts the synthetic transaction loop.

## Main Endpoints

- `GET /health`
- `GET /agents`
- `GET /agents/{agent_id}/balances`
- `GET /agents/{agent_id}/forecast`
- `GET /aggregate/forecast`
- `GET /agents/{agent_id}/transactions`
- `GET /alerts`
- `GET /alerts/{alert_id}`
- `POST /alerts/{alert_id}/acknowledge`
- `POST /alerts/{alert_id}/escalate`
- `POST /alerts/{alert_id}/resolve`
- `GET /cases/{case_id}`
- `PATCH /cases/{case_id}`
- `GET /simulation/status`
- `POST /simulation/seed`
- `POST /simulation/reset`
- `POST /simulation/degrade-feed`
- `POST /simulate/scenario`

## Checks

```bash
python -m pytest app/tests
```

The Pass 1 tests cover the forecaster, velocity-spike anomaly detector, routing table, and case workflow transitions.

## Notes

All data is synthetic and stored locally in `sust_hackathon.db`. Delete the database or call `POST /simulation/reset` to return to a clean seeded demo state.

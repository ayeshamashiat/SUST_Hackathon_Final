import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.seed import seed_users
from app.cases.engine import evaluate_all
from app.config import ALERT_EVAL_INTERVAL_SECONDS
from app.db import aggregator_session, init_aggregator_schema, shared_session
from app.routers import aggregate, alerts, auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aggregator-api")

_alert_loop_running = False
_alert_loop_task: asyncio.Task | None = None


def _run_alert_evaluation() -> None:
    with shared_session() as shared, aggregator_session() as agg:
        evaluate_all(shared, agg)


async def _alert_loop() -> None:
    global _alert_loop_running
    while _alert_loop_running:
        try:
            await asyncio.to_thread(_run_alert_evaluation)
        except Exception:
            # Same reliability lesson as sync-service's own loop: one bad
            # cycle must never silently kill background evaluation forever.
            logger.exception("evaluate_all() raised - will retry next cycle")
        await asyncio.sleep(ALERT_EVAL_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _alert_loop_running, _alert_loop_task
    init_aggregator_schema()
    with aggregator_session() as session:
        seed_users(session)
    _alert_loop_running = True
    _alert_loop_task = asyncio.create_task(_alert_loop())
    yield
    _alert_loop_running = False


app = FastAPI(title="Aggregator API (alerts, forecasts, anomaly detection)", lifespan=lifespan)

# Frontend compatibility: this is the only service the frontend talks to.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(aggregate.router)
app.include_router(alerts.router)


@app.get("/health")
def health():
    return {"status": "ok"}

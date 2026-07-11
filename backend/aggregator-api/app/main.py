from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.seed import seed_users
from app.db import aggregator_session, init_aggregator_schema
from app.routers import aggregate, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_aggregator_schema()
    with aggregator_session() as session:
        seed_users(session)
    yield


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


@app.get("/health")
def health():
    return {"status": "ok"}

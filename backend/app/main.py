from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api.agents import router as agents_router
from app.api.alerts import router as alerts_router
from app.api.cases import router as cases_router
from app.api.simulation import router as simulation_router
from app.core.database import engine, init_db
from app.simulation import engine as sim_engine
from app.simulation.seed import is_seeded, seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        if not is_seeded(session):
            seed(session)
    sim_engine.start()
    yield
    sim_engine.stop()


app = FastAPI(
    title="SUST Hackathon Backend - Multi-Provider Liquidity & Coordination Prototype",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Next.js dev falls back to the next free port (3001, 3002, ...) if 3000
    # is taken, so allow any localhost port in development rather than a
    # single hardcoded origin.
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router)
app.include_router(alerts_router)
app.include_router(cases_router)
app.include_router(simulation_router)


@app.get("/")
def read_root():
    return {"status": "ok", "service": "sust-hackathon-backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers import bkash, nagad, rocket, simulator
from app.seed import seed_all
from app.simulator import engine as sim_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_all()
    sim_engine.start()
    yield
    sim_engine.stop()


app = FastAPI(title="Provider API (bKash / Nagad / Rocket)", lifespan=lifespan)

app.include_router(bkash.router)
app.include_router(nagad.router)
app.include_router(rocket.router)
app.include_router(simulator.router)


@app.get("/health")
def health():
    return {"status": "ok"}

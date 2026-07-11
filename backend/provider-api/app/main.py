from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers import bkash, nagad, rocket
from app.seed import seed_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_all()
    yield


app = FastAPI(title="Provider API (bKash / Nagad / Rocket)", lifespan=lifespan)

app.include_router(bkash.router)
app.include_router(nagad.router)
app.include_router(rocket.router)


@app.get("/health")
def health():
    return {"status": "ok"}

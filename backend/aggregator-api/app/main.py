from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import aggregate

app = FastAPI(title="Aggregator API (alerts, forecasts, anomaly detection)")

# Frontend compatibility: this is the only service the frontend talks to.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(aggregate.router)


@app.get("/health")
def health():
    return {"status": "ok"}

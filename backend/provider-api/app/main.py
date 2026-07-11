from fastapi import FastAPI

app = FastAPI(title="Provider API (bKash / Nagad / Rocket / Simulator)")


@app.get("/health")
def health():
    return {"status": "ok"}

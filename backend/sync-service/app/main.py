from fastapi import FastAPI

app = FastAPI(title="Sync Service")


@app.get("/health")
def health():
    return {"status": "ok"}

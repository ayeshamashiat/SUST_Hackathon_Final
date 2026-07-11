import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import init_shared_schema
from app.sync import get_status, sync_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync-service")

_running = False
_task: asyncio.Task | None = None


async def _loop() -> None:
    global _running
    while _running:
        try:
            await asyncio.to_thread(sync_all)
        except Exception:
            # A single bad cycle (a dropped connection, a transient DB error)
            # must never permanently kill the background loop - this exact
            # failure mode happened during development: an exception during
            # a large sync cycle propagated out of sync_all() uncaught,
            # silently ending the loop forever with nothing in the logs to
            # explain why. Log it and retry next interval instead.
            logger.exception("sync_all() raised - will retry next cycle")
        await asyncio.sleep(settings.sync_poll_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _running, _task
    init_shared_schema()
    _running = True
    _task = asyncio.create_task(_loop())
    yield
    _running = False


app = FastAPI(title="Sync Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sync/status")
def sync_status():
    """Not required by the brief, but cheap to expose and useful for
    debugging/demoing the sync loop directly rather than only inferring its
    behavior from aggregator-api later."""
    return get_status()

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.models import Agent, DataFeedStatus
from app.schemas.schemas import DegradeFeedIn
from app.simulation import engine as sim_engine

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/status")
def status(session: Session = Depends(get_session)):
    agents = list(session.exec(select(Agent)))
    feeds = list(session.exec(select(DataFeedStatus)))
    return {
        "running": sim_engine.is_running(),
        "agent_count": len(agents),
        "degraded_feeds": [{"agent_id": f.agent_id, "provider_id": f.provider_id} for f in feeds if f.frozen],
    }


@router.post("/reset")
def reset():
    sim_engine.reset()
    return {"status": "reset"}


@router.post("/degrade-feed")
def degrade_feed(body: DegradeFeedIn):
    sim_engine.set_feed_frozen(
        body.agent_id,
        body.provider_id,
        body.degrade,
        note="Manually degraded for demo purposes." if body.degrade else None,
    )
    return {"status": "ok"}

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_user, require_roles
from app.models.models import Agent, DataFeedStatus, UserRole
from app.schemas.schemas import DegradeFeedIn
from app.simulation import engine as sim_engine
from app.simulation.seed import is_seeded, seed

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Demo/admin controls - any operations-hierarchy role except the outlet-scoped AGENT role.
_ADMIN_ROLES = (
    UserRole.FIELD_OFFICER,
    UserRole.AREA_MANAGER,
    UserRole.PROVIDER_OPS,
    UserRole.RISK_COMPLIANCE,
    UserRole.MANAGEMENT,
)


@router.get("/status")
def status(_current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    agents = list(session.exec(select(Agent)))
    feeds = list(session.exec(select(DataFeedStatus)))
    return {
        "running": sim_engine.is_running(),
        "agent_count": len(agents),
        "degraded_feeds": [{"agent_id": f.agent_id, "provider_id": f.provider_id} for f in feeds if f.frozen],
    }


@router.post("/seed")
def seed_data(_current_user=Depends(require_roles(*_ADMIN_ROLES)), session: Session = Depends(get_session)):
    if is_seeded(session):
        return {"status": "already_seeded"}
    seed(session)
    return {"status": "seeded"}


@router.post("/reset")
def reset(_current_user=Depends(require_roles(*_ADMIN_ROLES))):
    sim_engine.reset()
    return {"status": "reset"}


@router.post("/degrade-feed")
def degrade_feed(body: DegradeFeedIn, _current_user=Depends(require_roles(*_ADMIN_ROLES))):
    sim_engine.set_feed_frozen(
        body.agent_id,
        body.provider_id,
        body.degrade,
        note="Manually degraded for demo purposes." if body.degrade else None,
    )
    return {"status": "ok"}

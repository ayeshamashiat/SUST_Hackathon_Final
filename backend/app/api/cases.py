from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.cases.workflow import InvalidTransitionError, apply_update
from app.core.database import get_session
from app.models.models import Case, CaseEvent
from app.schemas.schemas import CaseEventOut, CaseOut, CaseUpdateIn

router = APIRouter(tags=["cases"])


@router.get("/cases/{case_id}", response_model=CaseOut)
def get_case(case_id: int, session: Session = Depends(get_session)):
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return _to_case_out(session, case)


@router.patch("/cases/{case_id}", response_model=CaseOut)
def update_case(case_id: int, body: CaseUpdateIn, session: Session = Depends(get_session)):
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    try:
        case = apply_update(session, case, body.status, body.note, body.actor)
    except InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _to_case_out(session, case)


def _to_case_out(session: Session, case: Case) -> CaseOut:
    events = list(session.exec(select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at)))
    return CaseOut(
        id=case.id,
        alert_id=case.alert_id,
        stakeholder_role=case.stakeholder_role,
        owner=case.owner,
        status=case.status,
        recommended_action=case.recommended_action,
        created_at=case.created_at,
        updated_at=case.updated_at,
        events=[
            CaseEventOut(id=e.id, event_type=e.event_type, note=e.note, actor=e.actor, created_at=e.created_at)
            for e in events
        ],
    )

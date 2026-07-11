from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.cases.workflow import InvalidTransitionError, apply_update
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.models import Alert, Case, CaseEvent, User, UserRole
from app.schemas.schemas import CaseEventOut, CaseOut, CaseUpdateIn

router = APIRouter(tags=["cases"])


def _get_case_and_alert(session: Session, case_id: int) -> tuple[Case, Alert]:
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    alert = session.get(Alert, case.alert_id)
    return case, alert


def _require_read_scope(user: User, alert: Alert) -> None:
    if user.role == UserRole.AGENT and alert.agent_id != user.agent_id:
        raise HTTPException(403, "Not authorized to view this case")
    if user.role == UserRole.PROVIDER_OPS and alert.provider_id != user.provider_id:
        raise HTTPException(403, "Not authorized to view this case")


def _require_update_scope(user: User, case: Case, alert: Alert) -> None:
    if user.role == UserRole.RISK_COMPLIANCE:
        return
    if user.role == UserRole.FIELD_OFFICER and case.stakeholder_role == "Field Officer":
        return
    if (
        user.role == UserRole.PROVIDER_OPS
        and case.stakeholder_role == "Provider Operations"
        and alert.provider_id == user.provider_id
    ):
        return
    raise HTTPException(403, "Not authorized to update this case")


@router.get("/cases/{case_id}", response_model=CaseOut)
def get_case(
    case_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    case, alert = _get_case_and_alert(session, case_id)
    _require_read_scope(current_user, alert)
    return _to_case_out(session, case)


@router.patch("/cases/{case_id}", response_model=CaseOut)
def update_case(
    case_id: int,
    body: CaseUpdateIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case, alert = _get_case_and_alert(session, case_id)
    _require_update_scope(current_user, case, alert)
    try:
        case = apply_update(session, case, body.status, body.note, current_user.display_name)
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

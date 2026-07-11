from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.models import Agent, Alert, AlertCategory, Case, CaseEvent, Provider, User, UserRole
from app.schemas.schemas import AlertOut, CaseEventOut, CaseOut

router = APIRouter(tags=["alerts"])


def _in_scope(user: User, alert: Alert) -> bool:
    if user.role == UserRole.AGENT and alert.agent_id != user.agent_id:
        return False
    if user.role == UserRole.PROVIDER_OPS and alert.provider_id != user.provider_id:
        return False
    return True


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    agent_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    category: Optional[AlertCategory] = None,
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.role == UserRole.AGENT:
        agent_id = current_user.agent_id
    if current_user.role == UserRole.PROVIDER_OPS:
        provider_id = current_user.provider_id

    stmt = select(Alert)
    if agent_id:
        stmt = stmt.where(Alert.agent_id == agent_id)
    if provider_id:
        stmt = stmt.where(Alert.provider_id == provider_id)
    if category:
        stmt = stmt.where(Alert.category == category)
    stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
    return [_to_alert_out(session, a) for a in session.exec(stmt)]


@router.get("/alerts/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    if not _in_scope(current_user, alert):
        raise HTTPException(403, "Not authorized to view this alert")
    return _to_alert_out(session, alert)


def _to_alert_out(session: Session, alert: Alert) -> AlertOut:
    agent = session.get(Agent, alert.agent_id)
    provider = session.get(Provider, alert.provider_id) if alert.provider_id else None
    case = session.exec(select(Case).where(Case.alert_id == alert.id)).one_or_none()

    case_out = None
    if case:
        events = list(
            session.exec(select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at))
        )
        case_out = CaseOut(
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

    return AlertOut(
        id=alert.id,
        category=alert.category.value,
        metric=alert.metric,
        severity=alert.severity,
        agent_id=alert.agent_id,
        agent_name=agent.name if agent else alert.agent_id,
        provider_id=alert.provider_id,
        provider_name=provider.name if provider else None,
        title=alert.title,
        message_en=alert.message_en,
        message_bn=alert.message_bn,
        evidence=alert.evidence,
        confidence=alert.confidence,
        confidence_note=alert.confidence_note,
        data_quality=alert.data_quality,
        created_at=alert.created_at,
        case=case_out,
    )

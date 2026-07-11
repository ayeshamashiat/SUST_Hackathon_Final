from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.database import get_session
from app.alerts.routing import get_routing
from app.cases.workflow import InvalidTransitionError, apply_update
from app.models.models import Agent, Alert, AlertCategory, AlertEvent, Case, CaseEvent, CaseStatus, Provider
from app.schemas.schemas import AlertActionIn, AlertEventOut, AlertOut, CaseEventOut, CaseOut

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    agent_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    category: Optional[AlertCategory] = None,
    limit: int = Query(50, le=200),
    session: Session = Depends(get_session),
):
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
def get_alert(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return _to_alert_out(session, alert)


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, body: AlertActionIn, session: Session = Depends(get_session)):
    return _apply_alert_action(session, alert_id, CaseStatus.ACKNOWLEDGED, "ACKNOWLEDGED", body)


@router.post("/alerts/{alert_id}/escalate", response_model=AlertOut)
def escalate_alert(alert_id: int, body: AlertActionIn, session: Session = Depends(get_session)):
    return _apply_alert_action(session, alert_id, CaseStatus.ESCALATED, "ESCALATED", body)


@router.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: int, body: AlertActionIn, session: Session = Depends(get_session)):
    return _apply_alert_action(session, alert_id, CaseStatus.RESOLVED, "RESOLVED", body)


def _apply_alert_action(
    session: Session, alert_id: int, status: CaseStatus, event_type: str, body: AlertActionIn
) -> AlertOut:
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    case = session.exec(select(Case).where(Case.alert_id == alert.id)).one_or_none()
    if not case:
        raise HTTPException(409, "Alert has no coordination case")

    owner_role = _owner_role_for(session, alert)
    if status == CaseStatus.ESCALATED:
        # A direct escalation is allowed at the alert API boundary, while the
        # case state machine remains strict and auditable.
        if case.status == CaseStatus.NEW:
            apply_update(session, case, CaseStatus.ACKNOWLEDGED, "Automatically acknowledged before escalation.", body.actor)
        case.stakeholder_role = "Risk Analyst"
        case.owner = "Risk Analyst (on duty)"
        owner_role = "risk_analyst"
        session.add(case)
        session.commit()

    try:
        apply_update(session, case, status, body.note, body.actor)
    except InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc

    session.add(
        AlertEvent(
            alert_id=alert.id,
            event_type=event_type,
            actor=body.actor,
            note=body.note,
            owner_role=owner_role,
        )
    )
    session.commit()
    return _to_alert_out(session, alert)


def _owner_role_for(session: Session, alert: Alert) -> str:
    provider = session.get(Provider, alert.provider_id) if alert.provider_id else None
    return get_routing(alert.category, alert.provider_id, provider.name if provider else None)["owner_role"]


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

    alert_events = list(
        session.exec(select(AlertEvent).where(AlertEvent.alert_id == alert.id).order_by(AlertEvent.created_at))
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
        message_banglish=alert.message_banglish,
        evidence=alert.evidence,
        confidence=alert.confidence,
        confidence_note=alert.confidence_note,
        data_quality=alert.data_quality,
        created_at=alert.created_at,
        case=case_out,
        events=[
            AlertEventOut(
                id=event.id,
                event_type=event.event_type,
                actor=event.actor,
                note=event.note,
                owner_role=event.owner_role,
                created_at=event.created_at,
            )
            for event in alert_events
        ],
    )

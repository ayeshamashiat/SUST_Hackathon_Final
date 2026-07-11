"""Alert assignment + case-lifecycle API - the stakeholder loop from the
brief's coordination requirement (Scenario D). Alerts are created by the
background engine (cases/engine.py); this router only lets the currently
assigned stakeholder move a case through acknowledge -> review -> {monitor,
escalate, resolve} -> close, with every action recorded to CaseEvent.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.auth.deps import get_current_user
from app.auth.models import User, UserRole
from app.cases import workflow
from app.cases.models import Alert, AlertType, CaseEvent, CaseStatus
from app.db import get_aggregator_db
from app.schemas import AddNoteIn, AIRecommendationOut, AlertActionIn, AlertOut, CaseEventOut, EscalateIn

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _can_read(user: User, alert: Alert) -> bool:
    if user.role == UserRole.AGENT:
        return alert.agent_id == user.agent_id
    if user.role == UserRole.PROVIDER_OPS:
        return alert.provider == user.provider_id
    return True  # FIELD_OFFICER, AREA_MANAGER, RISK_COMPLIANCE, MANAGEMENT: oversight roles, read everything


def _can_act(user: User, alert: Alert) -> bool:
    if user.role != alert.current_owner:
        return False
    if user.role == UserRole.AGENT and alert.agent_id != user.agent_id:
        return False
    if user.role == UserRole.PROVIDER_OPS and alert.provider != user.provider_id:
        return False
    return True


def _get_readable(session: Session, user: User, alert_id: int) -> Alert:
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    if not _can_read(user, alert):
        raise HTTPException(403, "Not authorized to view this alert")
    return alert


def _get_actionable(session: Session, user: User, alert_id: int) -> Alert:
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    if not _can_act(user, alert):
        raise HTTPException(403, "Not authorized to act on this case - it is not currently assigned to you")
    return alert


def _to_alert_out(session: Session, alert: Alert) -> AlertOut:
    events = list(session.exec(select(CaseEvent).where(CaseEvent.alert_id == alert.id).order_by(CaseEvent.created_at)))

    def _out(e: CaseEvent) -> CaseEventOut:
        return CaseEventOut(
            id=e.id,
            event_type=e.event_type,
            actor=e.actor,
            note=e.note,
            previous_owner=e.previous_owner,
            new_owner=e.new_owner,
            reason=e.reason,
            created_at=e.created_at,
        )

    all_events = [_out(e) for e in events]
    return AlertOut(
        id=alert.id,
        provider=alert.provider,
        agent_id=alert.agent_id,
        alert_type=alert.alert_type,
        metric=alert.metric,
        severity=alert.severity,
        confidence=alert.confidence,
        confidence_note=alert.confidence_note,
        evidence=alert.evidence,
        title=alert.title,
        message_en=alert.message_en,
        message_bn=alert.message_bn,
        message_banglish=alert.message_banglish,
        recommended_action=alert.recommended_action,
        ai_recommendation=(
            AIRecommendationOut(
                text=alert.ai_recommendation,
                source=alert.ai_recommendation_source,
                note=alert.ai_recommendation_note,
            )
            if alert.ai_recommendation is not None
            else None
        ),
        current_owner=alert.current_owner,
        current_status=alert.current_status,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        notes=[e for e in all_events if e.event_type == "NOTE_ADDED"],
        assignment_history=[e for e in all_events if e.event_type in ("ASSIGNED", "ESCALATED", "REASSIGNED")],
        audit_trail=all_events,
    )


@router.get("", response_model=list[AlertOut])
def list_alerts(
    agent_id: Optional[str] = None,
    provider: Optional[str] = None,
    alert_type: Optional[AlertType] = None,
    status: Optional[CaseStatus] = None,
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_aggregator_db),
):
    if current_user.role == UserRole.AGENT:
        agent_id = current_user.agent_id
    if current_user.role == UserRole.PROVIDER_OPS:
        provider = current_user.provider_id

    stmt = select(Alert)
    if agent_id:
        stmt = stmt.where(Alert.agent_id == agent_id)
    if provider:
        stmt = stmt.where(Alert.provider == provider)
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
    if status:
        stmt = stmt.where(Alert.current_status == status)
    stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
    return [_to_alert_out(session, a) for a in session.exec(stmt)]


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_aggregator_db)):
    alert = _get_readable(session, current_user, alert_id)
    return _to_alert_out(session, alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge(
    alert_id: int,
    body: AlertActionIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_aggregator_db),
):
    alert = _get_actionable(session, current_user, alert_id)
    try:
        workflow.acknowledge(session, alert, current_user.display_name, body.note)
    except workflow.InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _to_alert_out(session, alert)


@router.post("/{alert_id}/start-review", response_model=AlertOut)
def start_review(
    alert_id: int,
    body: AlertActionIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_aggregator_db),
):
    alert = _get_actionable(session, current_user, alert_id)
    try:
        workflow.start_review(session, alert, current_user.display_name, body.note)
    except workflow.InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _to_alert_out(session, alert)


@router.post("/{alert_id}/notes", response_model=AlertOut)
def add_note(
    alert_id: int,
    body: AddNoteIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_aggregator_db),
):
    alert = _get_actionable(session, current_user, alert_id)
    try:
        workflow.add_note(session, alert, current_user.display_name, body.message)
    except workflow.InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _to_alert_out(session, alert)


@router.post("/{alert_id}/monitor", response_model=AlertOut)
def monitor(
    alert_id: int,
    body: AlertActionIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_aggregator_db),
):
    alert = _get_actionable(session, current_user, alert_id)
    try:
        workflow.monitor(session, alert, current_user.display_name, body.note)
    except workflow.InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _to_alert_out(session, alert)


@router.post("/{alert_id}/resolve", response_model=AlertOut)
def resolve(
    alert_id: int,
    body: AlertActionIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_aggregator_db),
):
    alert = _get_actionable(session, current_user, alert_id)
    try:
        workflow.resolve(session, alert, current_user.display_name, body.note)
    except workflow.InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _to_alert_out(session, alert)


@router.post("/{alert_id}/close", response_model=AlertOut)
def close(
    alert_id: int,
    body: AlertActionIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_aggregator_db),
):
    alert = _get_actionable(session, current_user, alert_id)
    try:
        workflow.close(session, alert, current_user.display_name, body.note)
    except workflow.InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _to_alert_out(session, alert)


@router.post("/{alert_id}/escalate", response_model=AlertOut)
def escalate(
    alert_id: int,
    body: EscalateIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_aggregator_db),
):
    alert = _get_actionable(session, current_user, alert_id)
    try:
        workflow.escalate(session, alert, current_user.display_name, body.reason)
    except workflow.InvalidTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _to_alert_out(session, alert)

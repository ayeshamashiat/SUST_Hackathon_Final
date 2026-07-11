"""Alert lifecycle state machine + append-only audit-trail writer.

NEW -> ASSIGNED -> ACKNOWLEDGED -> UNDER_REVIEW -> {MONITORING, ESCALATED, RESOLVED}
MONITORING -> {UNDER_REVIEW, ESCALATED, RESOLVED}
ESCALATED is transient: escalate() reassigns current_owner to the next rung
of the ladder and lands back on UNDER_REVIEW in the same call - a client
never sets ESCALATED directly.
RESOLVED -> CLOSED (final confirmation step).

Every transition writes exactly one CaseEvent row; nothing is ever deleted
or edited, per the brief's auditability requirement.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.cases.models import Alert, CaseEvent, CaseStatus
from app.cases.routing import next_owner, recommended_action


class InvalidTransitionError(ValueError):
    pass


_ALLOWED: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.NEW: {CaseStatus.ASSIGNED},
    CaseStatus.ASSIGNED: {CaseStatus.ACKNOWLEDGED},
    CaseStatus.ACKNOWLEDGED: {CaseStatus.UNDER_REVIEW},
    CaseStatus.UNDER_REVIEW: {CaseStatus.MONITORING, CaseStatus.ESCALATED, CaseStatus.RESOLVED},
    CaseStatus.MONITORING: {CaseStatus.UNDER_REVIEW, CaseStatus.ESCALATED, CaseStatus.RESOLVED},
    CaseStatus.ESCALATED: {CaseStatus.UNDER_REVIEW},
    CaseStatus.RESOLVED: {CaseStatus.CLOSED},
    CaseStatus.CLOSED: set(),
}

_EVENT_TYPE_FOR_STATUS = {
    CaseStatus.ASSIGNED: "ASSIGNED",
    CaseStatus.ACKNOWLEDGED: "ACKNOWLEDGED",
    CaseStatus.UNDER_REVIEW: "REVIEW_STARTED",
    CaseStatus.MONITORING: "MONITORING",
    CaseStatus.RESOLVED: "RESOLVED",
    CaseStatus.CLOSED: "CLOSED",
}


def _write_event(session: Session, alert: Alert, event_type: str, actor: str, **fields) -> None:
    session.add(CaseEvent(alert_id=alert.id, event_type=event_type, actor=actor, created_at=datetime.utcnow(), **fields))


def _transition(session: Session, alert: Alert, new_status: CaseStatus, actor: str, note: Optional[str]) -> Alert:
    allowed = _ALLOWED.get(alert.current_status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(f"Cannot move a case from {alert.current_status.value} to {new_status.value}.")
    alert.current_status = new_status
    alert.updated_at = datetime.utcnow()
    session.add(alert)
    _write_event(session, alert, _EVENT_TYPE_FOR_STATUS[new_status], actor, note=note)
    session.commit()
    session.refresh(alert)
    return alert


def acknowledge(session: Session, alert: Alert, actor: str, note: Optional[str] = None) -> Alert:
    return _transition(session, alert, CaseStatus.ACKNOWLEDGED, actor, note)


def start_review(session: Session, alert: Alert, actor: str, note: Optional[str] = None) -> Alert:
    """ACKNOWLEDGED -> UNDER_REVIEW, or MONITORING -> UNDER_REVIEW (resuming a monitored case)."""
    return _transition(session, alert, CaseStatus.UNDER_REVIEW, actor, note)


def add_note(session: Session, alert: Alert, actor: str, message: str) -> Alert:
    if alert.current_status == CaseStatus.CLOSED:
        raise InvalidTransitionError("Cannot add a note to a closed case.")
    alert.updated_at = datetime.utcnow()
    session.add(alert)
    _write_event(session, alert, "NOTE_ADDED", actor, note=message)
    session.commit()
    session.refresh(alert)
    return alert


def monitor(session: Session, alert: Alert, actor: str, note: Optional[str] = None) -> Alert:
    return _transition(session, alert, CaseStatus.MONITORING, actor, note)


def resolve(session: Session, alert: Alert, actor: str, note: Optional[str] = None) -> Alert:
    return _transition(session, alert, CaseStatus.RESOLVED, actor, note)


def close(session: Session, alert: Alert, actor: str, note: Optional[str] = None) -> Alert:
    return _transition(session, alert, CaseStatus.CLOSED, actor, note)


def escalate(session: Session, alert: Alert, actor: str, reason: str) -> Alert:
    if CaseStatus.ESCALATED not in _ALLOWED.get(alert.current_status, set()):
        raise InvalidTransitionError(f"Cannot escalate a case in {alert.current_status.value}.")
    new_owner = next_owner(alert.current_owner)
    if new_owner is None:
        raise InvalidTransitionError("Already at the top of the escalation ladder (Management) - cannot escalate further.")

    old_owner = alert.current_owner
    now = datetime.utcnow()
    _write_event(session, alert, "ESCALATED", actor, reason=reason, previous_owner=old_owner, new_owner=new_owner)

    alert.current_owner = new_owner
    alert.current_status = CaseStatus.UNDER_REVIEW
    alert.recommended_action = recommended_action(alert.alert_type, new_owner, alert.provider)
    alert.updated_at = now
    session.add(alert)
    _write_event(session, alert, "REASSIGNED", "system", reason=reason, previous_owner=old_owner, new_owner=new_owner)

    session.commit()
    session.refresh(alert)
    return alert

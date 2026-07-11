"""Case status state machine + audit-trail writer.

Every status change (and every note) becomes a CaseEvent row, so a case's
full history - who did what, when - is reconstructable for the auditability
requirement.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.models.models import Case, CaseEvent, CaseStatus

ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.NEW: {CaseStatus.ACKNOWLEDGED, CaseStatus.IN_PROGRESS, CaseStatus.RESOLVED},
    CaseStatus.ACKNOWLEDGED: {CaseStatus.IN_PROGRESS, CaseStatus.ESCALATED, CaseStatus.RESOLVED},
    CaseStatus.IN_PROGRESS: {CaseStatus.ESCALATED, CaseStatus.RESOLVED},
    CaseStatus.ESCALATED: {CaseStatus.RESOLVED},
    CaseStatus.RESOLVED: set(),
}

_EVENT_TYPE_FOR_STATUS = {
    CaseStatus.ACKNOWLEDGED: "ACKNOWLEDGED",
    CaseStatus.ESCALATED: "ESCALATED",
    CaseStatus.RESOLVED: "RESOLVED",
}


class InvalidTransitionError(ValueError):
    pass


def apply_update(
    session: Session, case: Case, new_status: Optional[CaseStatus], note: Optional[str], actor: str
) -> Case:
    now = datetime.utcnow()

    if new_status is not None and new_status != case.status:
        allowed = ALLOWED_TRANSITIONS.get(case.status, set())
        if new_status not in allowed:
            raise InvalidTransitionError(f"Cannot move a case from {case.status.value} to {new_status.value}.")
        event_type = _EVENT_TYPE_FOR_STATUS.get(new_status, "STATUS_CHANGED")
        case.status = new_status
        case.updated_at = now
        session.add(case)
        session.add(CaseEvent(case_id=case.id, event_type=event_type, note=note, actor=actor, created_at=now))
    elif note:
        session.add(CaseEvent(case_id=case.id, event_type="NOTE", note=note, actor=actor, created_at=now))
        case.updated_at = now
        session.add(case)

    session.commit()
    session.refresh(case)
    return case

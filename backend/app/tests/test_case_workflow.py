import pytest
from sqlmodel import select

from app.cases.workflow import InvalidTransitionError, apply_update
from app.models.models import Case, CaseEvent, CaseStatus


@pytest.fixture
def case(session):
    c = Case(
        alert_id=1,
        stakeholder_role="Field Officer",
        owner="Field Officer (on duty)",
        status=CaseStatus.NEW,
        recommended_action="Arrange additional cash.",
    )
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def test_valid_transition_creates_event(session, case):
    updated = apply_update(session, case, CaseStatus.ACKNOWLEDGED, "on it", "field_officer_1")
    assert updated.status == CaseStatus.ACKNOWLEDGED
    events = list(session.exec(select(CaseEvent).where(CaseEvent.case_id == case.id)))
    assert len(events) == 1
    assert events[0].event_type == "ACKNOWLEDGED"
    assert events[0].actor == "field_officer_1"


def test_invalid_transition_raises(session, case):
    with pytest.raises(InvalidTransitionError):
        apply_update(session, case, CaseStatus.ESCALATED, None, "field_officer_1")


def test_note_only_update_does_not_change_status(session, case):
    updated = apply_update(session, case, None, "checked in with the agent", "field_officer_1")
    assert updated.status == CaseStatus.NEW
    events = list(session.exec(select(CaseEvent).where(CaseEvent.case_id == case.id)))
    assert len(events) == 1
    assert events[0].event_type == "NOTE"


def test_resolved_is_terminal(session, case):
    case = apply_update(session, case, CaseStatus.ACKNOWLEDGED, None, "a")
    case = apply_update(session, case, CaseStatus.RESOLVED, None, "a")
    assert case.status == CaseStatus.RESOLVED
    with pytest.raises(InvalidTransitionError):
        apply_update(session, case, CaseStatus.IN_PROGRESS, None, "a")


def test_full_audit_trail_is_reconstructable(session, case):
    case = apply_update(session, case, CaseStatus.ACKNOWLEDGED, "seen", "officer")
    case = apply_update(session, case, CaseStatus.IN_PROGRESS, "arranging cash", "officer")
    case = apply_update(session, case, CaseStatus.RESOLVED, "delivered extra float", "officer")
    events = list(session.exec(select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at)))
    assert [e.event_type for e in events] == ["ACKNOWLEDGED", "STATUS_CHANGED", "RESOLVED"]

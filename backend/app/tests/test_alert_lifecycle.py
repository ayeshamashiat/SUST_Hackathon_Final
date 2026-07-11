from sqlmodel import select

from app.api.alerts import _apply_alert_action
from app.models.models import Alert, AlertCategory, AlertEvent, Case, CaseStatus, ConfidenceLevel, DataQuality
from app.schemas.schemas import AlertActionIn


def _alert_with_case(session):
    alert = Alert(
        category=AlertCategory.ANOMALY,
        metric="velocity_spike",
        severity="HIGH",
        agent_id="testagent",
        provider_id="bkash",
        title="Unusual activity - requires review",
        message_en="Review required.",
        message_bn="Review required.",
        message_banglish="Review required.",
        evidence={"z_score": 4.2},
        confidence=ConfidenceLevel.HIGH,
        confidence_note="Test evidence.",
        data_quality=DataQuality.OK,
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    session.add(
        Case(
            alert_id=alert.id,
            stakeholder_role="Provider Operations",
            owner="bKash Operations Team",
            status=CaseStatus.NEW,
            recommended_action="Review evidence.",
        )
    )
    session.commit()
    return alert


def test_acknowledge_creates_alert_event(session):
    alert = _alert_with_case(session)
    result = _apply_alert_action(
        session, alert.id, CaseStatus.ACKNOWLEDGED, "ACKNOWLEDGED", AlertActionIn(actor="ops_1", note="Seen")
    )
    assert result.case.status == CaseStatus.ACKNOWLEDGED
    events = list(session.exec(select(AlertEvent).where(AlertEvent.alert_id == alert.id)))
    assert [(event.event_type, event.actor) for event in events] == [("ACKNOWLEDGED", "ops_1")]


def test_escalation_routes_to_risk_analyst_and_creates_alert_event(session):
    alert = _alert_with_case(session)
    result = _apply_alert_action(
        session, alert.id, CaseStatus.ESCALATED, "ESCALATED", AlertActionIn(actor="ops_1", note="Escalating")
    )
    assert result.case.status == CaseStatus.ESCALATED
    assert result.case.stakeholder_role == "Risk Analyst"
    assert result.events[0].owner_role == "risk_analyst"

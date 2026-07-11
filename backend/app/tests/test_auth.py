import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session
from app.main import app
from app.models.models import Alert, AlertCategory, Case, CaseStatus, ConfidenceLevel, DataQuality
from app.simulation.seed import DEMO_LOGIN_CODE, seed

# NOTE: TestClient is intentionally *not* used as a context manager here, so the app's
# lifespan (real-DB seeding + background simulation loop) never runs - only the
# request/response cycle, against the in-memory engine wired in via dependency override.


@pytest.fixture
def engine():
    # StaticPool keeps a single underlying connection alive so every Session(eng)
    # (one per request via the get_session override) sees the same in-memory DB.
    eng = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(eng)
    with Session(eng) as session:
        seed(session)
    return eng


@pytest.fixture
def client(engine):
    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client, username, login_code=DEMO_LOGIN_CODE):
    return client.post("/auth/login", data={"username": username, "password": login_code})


def _auth_headers(client, username):
    token = _login(client, username).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_case(engine, provider_id, stakeholder_role, owner):
    with Session(engine) as session:
        alert = Alert(
            category=AlertCategory.LIQUIDITY,
            metric="cash_burn_rate",
            severity="HIGH",
            agent_id="zindabazar",
            provider_id=provider_id,
            title="Test alert",
            message_en="test",
            message_bn="test",
            confidence=ConfidenceLevel.HIGH,
            confidence_note="",
            data_quality=DataQuality.OK,
        )
        session.add(alert)
        session.commit()
        session.refresh(alert)
        case = Case(
            alert_id=alert.id,
            stakeholder_role=stakeholder_role,
            owner=owner,
            status=CaseStatus.NEW,
            recommended_action="do something",
        )
        session.add(case)
        session.commit()
        session.refresh(case)
        return case.id


def test_login_success_returns_role_and_token(client):
    resp = _login(client, "field.officer")
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "FIELD_OFFICER"
    assert body["access_token"]


def test_login_wrong_password_rejected(client):
    resp = _login(client, "field.officer", login_code="wrong")
    assert resp.status_code == 401


def test_login_unknown_username_rejected(client):
    resp = _login(client, "nobody")
    assert resp.status_code == 401


def test_protected_endpoint_requires_token(client):
    resp = client.get("/agents")
    assert resp.status_code == 401


def test_agent_role_scoped_to_own_outlet(client):
    headers = _auth_headers(client, "agent.zindabazar")
    assert client.get("/agents/zindabazar/balances", headers=headers).status_code == 200
    assert client.get("/agents/shahjalal/balances", headers=headers).status_code == 403


def test_agent_list_only_shows_own_agent(client):
    headers = _auth_headers(client, "agent.zindabazar")
    resp = client.get("/agents", headers=headers)
    assert resp.status_code == 200
    ids = [a["id"] for a in resp.json()]
    assert ids == ["zindabazar"]


def test_provider_ops_balances_hide_other_providers(client):
    headers = _auth_headers(client, "ops.bkash")
    resp = client.get("/agents/zindabazar/balances", headers=headers)
    assert resp.status_code == 200
    provider_ids = [p["provider_id"] for p in resp.json()["providers"]]
    assert provider_ids == ["bkash"]


def test_provider_ops_can_only_patch_own_provider_case(client, engine):
    bkash_case_id = _create_case(engine, "bkash", "Provider Operations", "bKash Operations Team")
    nagad_case_id = _create_case(engine, "nagad", "Provider Operations", "Nagad Operations Team")

    headers = _auth_headers(client, "ops.bkash")
    resp_own = client.patch(f"/cases/{bkash_case_id}", json={"status": "ACKNOWLEDGED"}, headers=headers)
    assert resp_own.status_code == 200
    assert resp_own.json()["events"][0]["actor"] == "bKash Operations Team"

    resp_other = client.patch(f"/cases/{nagad_case_id}", json={"status": "ACKNOWLEDGED"}, headers=headers)
    assert resp_other.status_code == 403


def test_field_officer_can_patch_field_officer_case_not_provider_case(client, engine):
    field_case_id = _create_case(engine, None, "Field Officer", "Field Officer (on duty)")
    provider_case_id = _create_case(engine, "bkash", "Provider Operations", "bKash Operations Team")

    headers = _auth_headers(client, "field.officer")
    assert client.patch(f"/cases/{field_case_id}", json={"status": "ACKNOWLEDGED"}, headers=headers).status_code == 200
    assert (
        client.patch(f"/cases/{provider_case_id}", json={"status": "ACKNOWLEDGED"}, headers=headers).status_code
        == 403
    )


def test_risk_compliance_can_patch_any_case(client, engine):
    case_id = _create_case(engine, "rocket", "Provider Operations", "Rocket Operations Team")
    headers = _auth_headers(client, "risk.compliance")
    resp = client.patch(f"/cases/{case_id}", json={"status": "ACKNOWLEDGED"}, headers=headers)
    assert resp.status_code == 200


def test_management_read_only_cannot_patch_case(client, engine):
    case_id = _create_case(engine, "bkash", "Provider Operations", "bKash Operations Team")
    headers = _auth_headers(client, "management")
    resp = client.patch(f"/cases/{case_id}", json={"status": "ACKNOWLEDGED"}, headers=headers)
    assert resp.status_code == 403


def test_simulation_reset_forbidden_for_agent_role(client):
    headers = _auth_headers(client, "agent.zindabazar")
    resp = client.post("/simulation/reset", headers=headers)
    assert resp.status_code == 403

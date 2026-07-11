import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.models import Agent, CashDrawer, Provider, ProviderBalance


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def agent_setup(session):
    session.add(Provider(id="bkash", name="bKash", color="#E2136E"))
    session.add(Provider(id="nagad", name="Nagad", color="#F6921E"))
    session.add(Provider(id="rocket", name="Rocket", color="#6C2EB9"))
    session.add(Agent(id="testagent", name="Test Agent", area="TestArea"))
    session.add(CashDrawer(agent_id="testagent", balance=20_000.0))
    for provider_id in ("bkash", "nagad", "rocket"):
        session.add(ProviderBalance(agent_id="testagent", provider_id=provider_id, balance=20_000.0))
    session.commit()
    return session

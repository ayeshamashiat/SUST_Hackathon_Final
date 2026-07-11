from sqlmodel import Session, select

from app.models.models import Agent, CashDrawer, DataFeedStatus, Provider, ProviderBalance
from app.simulation.profiles import AGENT_PROFILES, PROVIDERS


def is_seeded(session: Session) -> bool:
    return session.exec(select(Agent)).first() is not None


def seed(session: Session) -> None:
    for provider_id, name, color in PROVIDERS:
        session.add(Provider(id=provider_id, name=name, color=color))

    for profile in AGENT_PROFILES.values():
        session.add(Agent(id=profile.agent_id, name=profile.name, area=profile.area))
        session.add(CashDrawer(agent_id=profile.agent_id, balance=profile.cash_start))
        for provider_id, _, _ in PROVIDERS:
            balance = profile.provider_balance_start.get(provider_id, 20_000.0)
            session.add(ProviderBalance(agent_id=profile.agent_id, provider_id=provider_id, balance=balance))
            session.add(DataFeedStatus(agent_id=profile.agent_id, provider_id=provider_id))

    session.commit()


def reset(session: Session) -> None:
    from app.models.models import Alert, Case, CaseEvent, Transaction

    for model in (CaseEvent, Case, Alert, Transaction, DataFeedStatus, ProviderBalance, CashDrawer, Agent, Provider):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.commit()
    seed(session)

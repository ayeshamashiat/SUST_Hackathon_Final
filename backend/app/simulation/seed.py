import os

from sqlmodel import Session, select

from app.core.security import hash_password
from app.models.models import Agent, CashDrawer, DataFeedStatus, Provider, ProviderBalance, User, UserRole
from app.simulation.profiles import AGENT_PROFILES, PROVIDERS

# Predetermined operations-hierarchy logins (Section 5 of the brief). No self-registration
# and no customer accounts - see docs/CREDENTIALS.md for the full table shared with demo users.
DEMO_LOGIN_CODE = os.environ.get("DEMO_LOGIN_CODE", "Passw0rd!")

_USER_SEEDS: list[dict] = [
    *[
        {
            "username": f"agent.{profile.agent_id}",
            "role": UserRole.AGENT,
            "display_name": f"{profile.name} (Agent)",
            "agent_id": profile.agent_id,
            "provider_id": None,
        }
        for profile in AGENT_PROFILES.values()
    ],
    {
        "username": "field.officer",
        "role": UserRole.FIELD_OFFICER,
        "display_name": "Field Officer",
        "agent_id": None,
        "provider_id": None,
    },
    {
        "username": "area.manager",
        "role": UserRole.AREA_MANAGER,
        "display_name": "Area Manager",
        "agent_id": None,
        "provider_id": None,
    },
    *[
        {
            "username": f"ops.{provider_id}",
            "role": UserRole.PROVIDER_OPS,
            "display_name": f"{name} Operations Team",
            "agent_id": None,
            "provider_id": provider_id,
        }
        for provider_id, name, _ in PROVIDERS
    ],
    {
        "username": "risk.compliance",
        "role": UserRole.RISK_COMPLIANCE,
        "display_name": "Risk & Compliance Analyst",
        "agent_id": None,
        "provider_id": None,
    },
    {
        "username": "management",
        "role": UserRole.MANAGEMENT,
        "display_name": "Management",
        "agent_id": None,
        "provider_id": None,
    },
]


def is_seeded(session: Session) -> bool:
    return session.exec(select(Agent)).first() is not None


def seed(session: Session) -> None:
    for provider_id, name, color in PROVIDERS:
        session.add(Provider(id=provider_id, name=name, color=color))
    session.commit()

    for profile in AGENT_PROFILES.values():
        session.add(Agent(id=profile.agent_id, name=profile.name, area=profile.area))
        session.add(CashDrawer(agent_id=profile.agent_id, balance=profile.cash_start))
        for provider_id, _, _ in PROVIDERS:
            balance = profile.provider_balance_start.get(provider_id, 20_000.0)
            session.add(ProviderBalance(agent_id=profile.agent_id, provider_id=provider_id, balance=balance))
            session.add(DataFeedStatus(agent_id=profile.agent_id, provider_id=provider_id))

    session.commit()
    seed_users(session)


def seed_users(session: Session) -> None:
    password_hash = hash_password(DEMO_LOGIN_CODE)
    for spec in _USER_SEEDS:
        session.add(User(password_hash=password_hash, **spec))
    session.commit()


def reset(session: Session) -> None:
    from app.models.models import Alert, AlertEvent, Case, CaseEvent, Transaction

    for model in (
        AlertEvent,
        CaseEvent,
        Case,
        Alert,
        Transaction,
        DataFeedStatus,
        ProviderBalance,
        CashDrawer,
        User,
        Agent,
        Provider,
    ):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.commit()
    seed(session)

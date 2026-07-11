"""Predetermined operations-hierarchy logins (brief Section 5). No self-
registration and no customer accounts. Mirrors provider-api/app/seed_data.py's
agent list and services/cash.py's PROVIDERS - kept as a small local copy
rather than a cross-service import, same reasoning as sync-service's
provider_models.py: independently deployable services share a data
contract, not Python code.
"""

from sqlmodel import Session, select

from app.auth.models import User, UserRole
from app.auth.security import hash_password
from app.config import settings
from app.services.cash import PROVIDERS

_AGENT_IDS = [f"agent-{i:03d}" for i in range(1, 16)]

_PROVIDER_DISPLAY_NAME = {"bkash": "bKash", "nagad": "Nagad", "rocket": "Rocket"}


def _user_seeds() -> list[dict]:
    return [
        *[
            {
                "username": f"agent.{agent_id}",
                "role": UserRole.AGENT,
                "display_name": f"{agent_id} (Agent)",
                "agent_id": agent_id,
                "provider_id": None,
            }
            for agent_id in _AGENT_IDS
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
                "display_name": f"{_PROVIDER_DISPLAY_NAME[provider_id]} Operations Team",
                "agent_id": None,
                "provider_id": provider_id,
            }
            for provider_id in PROVIDERS
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
    return session.exec(select(User)).first() is not None


def seed_users(session: Session) -> None:
    if is_seeded(session):
        return
    password_hash = hash_password(settings.demo_login_code)
    for spec in _user_seeds():
        session.add(User(password_hash=password_hash, **spec))
    session.commit()

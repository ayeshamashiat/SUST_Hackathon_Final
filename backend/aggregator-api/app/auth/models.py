"""aggregator_db schema: users. Lives in aggregator-api's own database (see
db.py's module docstring) - not a provider-sync projection, so it's exempt
from shared_db's read-only rule by construction, not by exception.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.utcnow()


class UserRole(str, Enum):
    """The operations hierarchy from the brief (Section 5): outlet -> field/
    territory officer -> area/district manager -> provider operations team,
    plus risk/compliance and management oversight. Customers are never a
    login (Section 5) - not modeled here."""

    AGENT = "AGENT"
    FIELD_OFFICER = "FIELD_OFFICER"
    AREA_MANAGER = "AREA_MANAGER"
    PROVIDER_OPS = "PROVIDER_OPS"
    RISK_COMPLIANCE = "RISK_COMPLIANCE"
    MANAGEMENT = "MANAGEMENT"


class User(SQLModel, table=True):
    """A predetermined operations-hierarchy login (Section 5). No self-
    registration; accounts are created by the seed script only."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    role: UserRole
    display_name: str
    agent_id: Optional[str] = Field(default=None)  # AGENT role scope - no FK, agents live in a different service's DB
    provider_id: Optional[str] = Field(default=None)  # PROVIDER_OPS role scope (bkash/nagad/rocket)
    created_at: datetime = Field(default_factory=utcnow)

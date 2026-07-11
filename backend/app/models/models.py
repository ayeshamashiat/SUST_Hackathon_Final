from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.utcnow()


class TransactionType(str, Enum):
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"


class TransactionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class FeedHealth(str, Enum):
    OK = "OK"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DataQuality(str, Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"


class AlertCategory(str, Enum):
    LIQUIDITY = "LIQUIDITY"
    ANOMALY = "ANOMALY"
    DATA_QUALITY = "DATA_QUALITY"


class CaseStatus(str, Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"


class Provider(SQLModel, table=True):
    """A logically separate mobile financial service provider (bKash/Nagad/Rocket).

    Kept as its own table (rather than a hardcoded enum) so provider balances
    can never be summed or converted in code - they only ever join on this id.
    """

    id: str = Field(primary_key=True)  # e.g. "bkash"
    name: str
    color: str


class Agent(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    area: str


class CashDrawer(SQLModel, table=True):
    """Shared physical cash reserve - one per agent, never per provider."""

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(foreign_key="agent.id", unique=True, index=True)
    balance: float
    updated_at: datetime = Field(default_factory=utcnow)


class ProviderBalance(SQLModel, table=True):
    """One e-money balance per (agent, provider) - never merged across providers."""

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(foreign_key="agent.id", index=True)
    provider_id: str = Field(foreign_key="provider.id", index=True)
    balance: float
    updated_at: datetime = Field(default_factory=utcnow)


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(foreign_key="agent.id", index=True)
    provider_id: str = Field(foreign_key="provider.id", index=True)
    type: TransactionType
    amount: float
    customer_ref: str
    area: str
    status: TransactionStatus = TransactionStatus.SUCCESS
    created_at: datetime = Field(default_factory=utcnow, index=True)


class DataFeedStatus(SQLModel, table=True):
    """Tracks freshness/health of each (agent, provider) feed for safe fallback."""

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(foreign_key="agent.id", index=True)
    provider_id: str = Field(foreign_key="provider.id", index=True)
    health: FeedHealth = FeedHealth.OK
    last_update_at: datetime = Field(default_factory=utcnow)
    note: Optional[str] = None
    frozen: bool = False  # manually degraded via /simulation for demo purposes


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: AlertCategory
    metric: str  # e.g. "cash_burn_rate", "velocity_spike"
    severity: str  # LOW / MEDIUM / HIGH
    agent_id: str = Field(foreign_key="agent.id", index=True)
    provider_id: Optional[str] = Field(default=None, foreign_key="provider.id")  # None = shared cash
    title: str
    message_en: str
    message_bn: str
    evidence: dict = Field(default_factory=dict, sa_column=Column(JSON))
    confidence: ConfidenceLevel
    confidence_note: str
    data_quality: DataQuality = DataQuality.OK
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Case(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alert_id: int = Field(foreign_key="alert.id", unique=True, index=True)
    stakeholder_role: str
    owner: str
    status: CaseStatus = CaseStatus.NEW
    recommended_action: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class CaseEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    event_type: str  # CREATED / ACKNOWLEDGED / STATUS_CHANGED / NOTE / ESCALATED / RESOLVED
    note: Optional[str] = None
    actor: str
    created_at: datetime = Field(default_factory=utcnow)

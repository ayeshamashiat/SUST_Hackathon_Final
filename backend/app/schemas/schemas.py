from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, PlainSerializer

from app.core.time import to_utc_iso
from app.models.models import CaseStatus, ConfidenceLevel, DataQuality, FeedHealth, UserRole

UTCDateTime = Annotated[datetime, PlainSerializer(to_utc_iso, return_type=str, when_used="json")]


class ProviderBalanceOut(BaseModel):
    provider_id: str
    provider_name: str
    color: str
    balance: float
    feed_health: FeedHealth
    feed_last_update_at: UTCDateTime


class AgentBalancesOut(BaseModel):
    agent_id: str
    agent_name: str
    area: str
    cash_balance: float
    cash_updated_at: UTCDateTime
    providers: list[ProviderBalanceOut]


class ForecastOut(BaseModel):
    target: str  # "CASH" or a provider_id
    target_label: str
    status: str  # "STABLE" | "AT_RISK" | "INSUFFICIENT_DATA"
    current_balance: float
    burn_rate_per_minute: Optional[float] = None
    projected_shortage_at: Optional[UTCDateTime] = None
    minutes_to_shortage: Optional[float] = None
    confidence: ConfidenceLevel
    confidence_note: str
    data_quality: DataQuality
    top_contributors: list[dict] = []
    message_en: str
    message_bn: str


class CaseEventOut(BaseModel):
    id: int
    event_type: str
    note: Optional[str]
    actor: str
    created_at: UTCDateTime


class CaseOut(BaseModel):
    id: int
    alert_id: int
    stakeholder_role: str
    owner: str
    status: CaseStatus
    recommended_action: str
    created_at: UTCDateTime
    updated_at: UTCDateTime
    events: list[CaseEventOut] = []


class AlertOut(BaseModel):
    id: int
    category: str
    metric: str
    severity: str
    agent_id: str
    agent_name: str
    provider_id: Optional[str]
    provider_name: Optional[str]
    title: str
    message_en: str
    message_bn: str
    evidence: dict
    confidence: ConfidenceLevel
    confidence_note: str
    data_quality: DataQuality
    created_at: UTCDateTime
    case: Optional[CaseOut] = None


class CaseUpdateIn(BaseModel):
    status: Optional[CaseStatus] = None
    note: Optional[str] = None


class DegradeFeedIn(BaseModel):
    agent_id: str
    provider_id: str
    degrade: bool


class UserOut(BaseModel):
    username: str
    role: UserRole
    display_name: str
    agent_id: Optional[str] = None
    provider_id: Optional[str] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    display_name: str
    agent_id: Optional[str] = None
    provider_id: Optional[str] = None

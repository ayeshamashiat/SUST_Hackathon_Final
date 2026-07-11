from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.services.confidence import ConfidenceLevel


class ProviderBalanceOut(BaseModel):
    provider: str
    balance: Optional[float]
    staleness_seconds: Optional[float]
    sync_status: Optional[str]
    confidence: ConfidenceLevel
    confidence_note: str


class AgentAggregateOut(BaseModel):
    agent_id: str
    cash_balance: float
    cash_confidence: ConfidenceLevel
    cash_confidence_note: str
    providers: list[ProviderBalanceOut]
    overall_confidence: ConfidenceLevel


class ForecastOut(BaseModel):
    target: str
    target_label: str
    status: str
    current_balance: float
    burn_rate_per_minute: Optional[float] = None
    projected_shortage_at: Optional[datetime] = None
    minutes_to_shortage: Optional[float] = None
    confidence: ConfidenceLevel
    confidence_note: str
    top_contributors: list[dict] = []


class AnomalyOut(BaseModel):
    agent_id: str
    provider: str
    flagged: bool
    window_count: int
    baseline_mean: float
    baseline_stdev: float
    z_score: Optional[float]
    unique_customers: int
    concentration_ratio: Optional[float]
    amount_min: float
    amount_max: float
    amount_coefficient_of_variation: Optional[float]
    sample_transaction_ids: list[int]
    window_start: Optional[datetime]
    window_end: Optional[datetime]
    confidence: ConfidenceLevel
    message: str

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


class AIRecommendationOut(BaseModel):
    text: str
    source: str  # "ai" | "fallback"
    note: Optional[str] = None


class AlertOut(BaseModel):
    category: str  # LIQUIDITY | ANOMALY
    metric: str
    severity: str  # LOW | MEDIUM | HIGH
    agent_id: str
    provider: Optional[str]  # None = shared cash
    title: str
    message: str
    evidence: dict
    confidence: ConfidenceLevel
    confidence_note: str
    recommended_action: str
    ai_recommendation: AIRecommendationOut


class AmountOutlierOut(BaseModel):
    """Is this agent's most recent transaction unusual for THIS agent
    specifically, given their own historical pattern - distinct from
    AnomalyOut above, which looks at burst frequency/clustering, not a
    single transaction's amount against one agent's history."""

    agent_id: str
    provider: str
    transaction_type: str
    flagged: bool
    evaluated_transaction_id: Optional[int]
    evaluated_amount: Optional[float]
    evaluated_at: Optional[datetime]
    historical_sample_size: int
    historical_mean: Optional[float]
    historical_stdev: Optional[float]
    z_score: Optional[float]
    confidence: ConfidenceLevel
    message: str

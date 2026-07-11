from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.seed_data import PROVIDERS


class SimulateRunIn(BaseModel):
    mode: Literal["normal", "eid_spike"] = "normal"
    providers: list[str] = Field(default_factory=lambda: list(PROVIDERS))
    agent_ids: Optional[list[str]] = None  # None = all seeded agents
    count: Optional[int] = None  # per-agent transaction count for the immediate batch; mode default if omitted
    duration_minutes: float = 0.0  # if > 0, also sets the background loop's ambient mode for this long
    multiplier: float = 1.0  # scales volume/frequency while the ambient scenario is active


class SimulateRunOut(BaseModel):
    mode: str
    generated_per_provider: dict
    total_generated: int
    ambient_scenario_until: Optional[datetime] = None


class InjectAnomalyIn(BaseModel):
    provider: str
    agent_id: str
    count: int = Field(8, ge=1, le=50)
    window_seconds: float = Field(120.0, gt=0)
    amount: float = Field(5_000.0, gt=0)
    amount_jitter: float = Field(50.0, ge=0)
    account_pool_size: int = Field(3, ge=1, le=10)


class InjectAnomalyOut(BaseModel):
    provider: str
    agent_id: str
    transactions_created: int
    window_seconds: float
    note: str = "Synthetic pattern generated for anomaly-detector testing. Not a fraud determination."


class FeedDelayIn(BaseModel):
    provider: str
    delay: bool = True
    note: Optional[str] = None


class FeedDelayOut(BaseModel):
    provider: str
    delayed: bool
    paused_providers: list[str]


class SimulatorStatusOut(BaseModel):
    running: bool
    started_at: Optional[datetime]
    last_tick_at: Optional[datetime]
    paused_providers: list[str]
    ambient_scenario: Optional[dict]
    transactions_generated: dict
    last_anomaly_injected_at: dict

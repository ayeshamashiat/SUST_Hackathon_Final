"""In-memory simulator state.

Single-process, not persisted - a restart resets pause flags and the active
scenario back to defaults. That's an acceptable tradeoff for a hackathon demo
control plane (not the transaction data itself, which lives in Postgres and
survives restarts). Scoped to provider-api only; nothing here is written to
shared_db.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.seed_data import PROVIDERS


@dataclass
class ScenarioState:
    mode: str = "normal"  # "normal" | "eid_spike"
    multiplier: float = 1.0
    until: Optional[datetime] = None


@dataclass
class SimulatorState:
    running: bool = False
    started_at: Optional[datetime] = None
    last_tick_at: Optional[datetime] = None
    paused_providers: set = field(default_factory=set)
    scenario: ScenarioState = field(default_factory=ScenarioState)
    tx_counts: dict = field(default_factory=lambda: {p: 0 for p in PROVIDERS})
    last_anomaly_injected_at: dict = field(default_factory=lambda: {p: None for p in PROVIDERS})


state = SimulatorState()

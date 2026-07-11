"""Alert + case-lifecycle schema, owned by aggregator-api's own aggregator_db
(same reasoning as auth/models.py: not a provider-sync projection, so it's
exempt from shared_db's read-only rule by construction).

Deliberately ONE case-lifecycle table (Alert) plus ONE audit table
(CaseEvent) rather than separate Alert/Case/CaseNote/AssignmentHistory
tables: current_owner and current_status live directly on Alert (per the
brief's "Required Fields" list), and CaseEvent is a generic append-only
event log whose rows serve as case notes (event_type=NOTE_ADDED), assignment
history (event_type in {ASSIGNED, ESCALATED, REASSIGNED}), and the full
audit trail (every row, in order) - the API layer (routers/alerts.py)
exposes these as three distinct filtered views without needing three
distinct tables to never delete from.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.auth.models import UserRole
from app.services.confidence import ConfidenceLevel


def utcnow() -> datetime:
    return datetime.utcnow()


class AlertType(str, Enum):
    LIQUIDITY = "LIQUIDITY"
    ANOMALY = "ANOMALY"
    DATA_QUALITY = "DATA_QUALITY"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CaseStatus(str, Enum):
    """NEW -> ASSIGNED happens atomically at creation (the engine never
    leaves an alert sitting in NEW - see cases/engine.py). From ASSIGNED:
    ACKNOWLEDGED -> UNDER_REVIEW -> {MONITORING, ESCALATED, RESOLVED}.
    ESCALATED immediately reassigns current_owner and moves back to
    UNDER_REVIEW under the new owner (cases/workflow.py:escalate) - it is
    never a resting state a client sets directly. RESOLVED -> CLOSED is a
    separate, final confirmation step."""

    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_REVIEW = "UNDER_REVIEW"
    MONITORING = "MONITORING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # --- what was detected ---
    provider: Optional[str] = None  # None = shared cash reserve, not any single provider
    agent_id: str = Field(index=True)
    alert_type: AlertType
    metric: str  # e.g. "cash_burn_rate", "provider_burn_rate", "velocity_spike", "amount_outlier", "feed_sync_status"
    severity: Severity
    confidence: ConfidenceLevel
    confidence_note: str
    evidence: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # --- advisory narrative (never a fraud/financial determination) ---
    title: str
    message_en: str
    message_bn: str
    message_banglish: str = ""
    recommended_action: str

    # --- Phase 8: additive AI-generated recommendation (services/llm.py) -
    # never changes alert_type/severity/current_owner above, which are all
    # decided by the rule-based detectors and routing.py before this even
    # runs. None for alert types llm.py doesn't cover yet (e.g. DATA_QUALITY),
    # or if the recommendation text hasn't been computed for some reason.
    ai_recommendation: Optional[str] = None
    ai_recommendation_source: Optional[str] = None  # "ai" | "fallback"
    ai_recommendation_note: Optional[str] = None

    # --- ownership + lifecycle (the assignment loop) ---
    current_owner: UserRole
    current_status: CaseStatus = CaseStatus.NEW

    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow)


class CaseEvent(SQLModel, table=True):
    """Append-only audit trail. Nothing is ever deleted or updated here -
    every acknowledgement, note, reassignment, and status change is a new
    row, so a case's full history is reconstructable from this table alone."""

    id: Optional[int] = Field(default=None, primary_key=True)
    alert_id: int = Field(foreign_key="alert.id", index=True)

    # CREATED / ASSIGNED / ACKNOWLEDGED / REVIEW_STARTED / NOTE_ADDED /
    # MONITORING / ESCALATED / REASSIGNED / RESOLVED / CLOSED
    event_type: str
    actor: str  # display name of the acting user, or "system"

    note: Optional[str] = None  # case-note message, or a free-text detail on any event
    previous_owner: Optional[UserRole] = None  # populated for ASSIGNED / ESCALATED / REASSIGNED
    new_owner: Optional[UserRole] = None
    reason: Optional[str] = None  # populated for ESCALATED / REASSIGNED

    created_at: datetime = Field(default_factory=utcnow, index=True)

"""shared_db schema. sync-service is the only service that creates or writes
these tables - aggregator-api (Phase 5) will get a read-only Postgres role
against the same database, enforced at the permission layer (see
db-init/init-databases.sh), not just by convention.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


def utcnow() -> datetime:
    return datetime.utcnow()


class SyncStatus(str, Enum):
    OK = "ok"
    DELAYED = "delayed"
    FAILED = "failed"
    CONFLICTING = "conflicting"


class ProviderBalance(SQLModel, table=True):
    """Current projected e-money balance per (agent, provider) - one row per
    pair, upserted every sync cycle. `staleness_seconds`/`sync_status` are
    exactly the mechanism the brief requires for lowering forecast
    confidence when a provider's data is missing, late, or inconsistent
    (wired into confidence scoring in Phase 5 - stored here so that phase has
    something real to read, not something it has to invent)."""

    __tablename__ = "provider_balances"
    __table_args__ = (UniqueConstraint("agent_id", "provider", name="uq_provider_balances_agent_provider"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(index=True)
    provider: str = Field(index=True)
    emoney_balance: float
    source_updated_at: datetime  # the provider's own balances.last_updated - freshness of the SOURCE, not of our poll
    synced_at: datetime = Field(default_factory=utcnow)  # when sync-service last wrote this row
    staleness_seconds: float
    sync_status: SyncStatus


class TransactionProjection(SQLModel, table=True):
    """Append-only projection of provider transactions. `provider_txn_id` is
    only unique within one provider's own database, so the dedup key is the
    (provider, provider_txn_id) pair, not provider_txn_id alone."""

    __tablename__ = "transactions_projection"
    __table_args__ = (UniqueConstraint("provider", "provider_txn_id", name="uq_txproj_provider_txnid"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    provider_txn_id: int
    agent_id: str = Field(index=True)
    provider: str = Field(index=True)
    type: str
    amount: float
    account_ref: str
    occurred_at: datetime = Field(index=True)  # the provider's own transaction timestamp
    synced_at: datetime = Field(default_factory=utcnow)
    # Internal-only, carried through for Phase 7's offline anomaly-detector
    # validation. Never exposed by any aggregator-api endpoint.
    is_injected_anomaly: bool = False


class SyncState(SQLModel, table=True):
    """Per-provider bookkeeping: the transaction-id watermark that makes
    polling incremental (and idempotent - never refetch/reproject a
    transaction id already synced), plus enough poll-attempt history to
    detect a `failed` provider (a poll that raised, not just one that was
    slow)."""

    __tablename__ = "sync_state"

    provider: str = Field(primary_key=True)
    last_synced_txn_id: int = 0
    last_poll_attempt_at: Optional[datetime] = None
    last_poll_success_at: Optional[datetime] = None
    consecutive_failures: int = 0

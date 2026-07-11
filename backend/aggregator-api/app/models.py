"""Read-only mirror of sync-service's shared_db schema (sync-service/app/
models.py). Duplicated rather than imported across the service boundary -
same reasoning as sync-service's own provider_models.py: independently
deployable services share a DB contract, not Python code. aggregator-api
never calls create_all against this - sync-service owns and creates this
schema; this service's Postgres role (shared_service) is SELECT-only by
grant, not just by convention (see db-init/init-databases.sh).
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class SyncStatus(str, Enum):
    OK = "ok"
    DELAYED = "delayed"
    FAILED = "failed"
    CONFLICTING = "conflicting"


class ProviderBalance(SQLModel, table=True):
    __tablename__ = "provider_balances"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str
    provider: str
    emoney_balance: float
    source_updated_at: datetime
    synced_at: datetime
    staleness_seconds: float
    sync_status: SyncStatus


class TransactionProjection(SQLModel, table=True):
    __tablename__ = "transactions_projection"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider_txn_id: int
    agent_id: str
    provider: str
    type: str
    amount: float
    account_ref: str
    occurred_at: datetime
    synced_at: datetime
    is_injected_anomaly: bool = False


class SyncState(SQLModel, table=True):
    __tablename__ = "sync_state"

    provider: str = Field(primary_key=True)
    last_synced_txn_id: int = 0
    last_poll_attempt_at: Optional[datetime] = None
    last_poll_success_at: Optional[datetime] = None
    consecutive_failures: int = 0

"""Per-provider database schema.

The SAME table definitions are applied to three physically separate
databases (bkash_db, nagad_db, rocket_db) via three independent engines in
db.py - this file has no notion of "which provider," that's determined
entirely by which engine a session was opened against. A `provider` column
is still stored on each row (redundant with "which DB this is," but kept
because the challenge brief's schema asks for it explicitly and it makes rows
self-describing if ever inspected directly).
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.utcnow()


class TransactionType(str, Enum):
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"


class Balance(SQLModel, table=True):
    __tablename__ = "balances"

    agent_id: str = Field(primary_key=True)
    provider: str
    emoney_balance: float
    last_updated: datetime = Field(default_factory=utcnow)


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    txn_id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(index=True)
    provider: str
    type: TransactionType
    amount: float
    account_ref: str
    timestamp: datetime = Field(default_factory=utcnow, index=True)
    # Internal-only label for offline anomaly-detector validation (Phase 7).
    # Never returned by any endpoint in this service.
    is_injected_anomaly: bool = False

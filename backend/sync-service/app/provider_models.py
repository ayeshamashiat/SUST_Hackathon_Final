"""Read-only mirror of provider-api's schema (app/models.py there).

Deliberately duplicated rather than imported across the service boundary -
sync-service and provider-api are independently deployable, so they don't
share Python code, only a database contract (table/column names). This
service never calls `create_all` against a provider engine and never writes
to these tables - provider-api owns that schema; this is read-only.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionType(str, Enum):
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"


class Balance(SQLModel, table=True):
    __tablename__ = "balances"

    agent_id: str = Field(primary_key=True)
    provider: str
    emoney_balance: float
    last_updated: datetime


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    txn_id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str
    provider: str
    type: TransactionType
    amount: float
    account_ref: str
    timestamp: datetime
    is_injected_anomaly: bool = False

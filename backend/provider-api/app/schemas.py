from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models import TransactionType


class BalanceOut(BaseModel):
    provider: str
    agent_id: str
    balance: float
    last_updated: datetime


class TransactionOut(BaseModel):
    """Deliberately excludes `is_injected_anomaly` - that flag exists only
    for offline anomaly-detector validation (Phase 7) and must never reach a
    customer/demo-facing endpoint."""

    txn_id: int
    agent_id: str
    provider: str
    type: TransactionType
    amount: float
    account_ref: str
    timestamp: datetime

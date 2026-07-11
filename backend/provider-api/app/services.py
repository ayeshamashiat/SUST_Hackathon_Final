"""Provider-agnostic query logic, reused by all three provider routers.

Nothing here knows which provider it's serving beyond the `provider` string
passed in for labeling the response - the actual isolation comes from which
`Session` (bound to which engine) the router handed it, not from anything in
this module. This is what lets bkash/nagad/rocket share one implementation
without sharing data access.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import Balance, Transaction, TransactionType


def get_balance(session: Session, agent_id: str) -> Optional[Balance]:
    return session.get(Balance, agent_id)


def list_transactions(
    session: Session,
    agent_id: str,
    limit: int = 50,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[TransactionType] = None,
) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.agent_id == agent_id)
    if start_date is not None:
        stmt = stmt.where(Transaction.timestamp >= start_date)
    if end_date is not None:
        stmt = stmt.where(Transaction.timestamp <= end_date)
    if transaction_type is not None:
        stmt = stmt.where(Transaction.type == transaction_type)
    stmt = stmt.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit)
    return list(session.exec(stmt))

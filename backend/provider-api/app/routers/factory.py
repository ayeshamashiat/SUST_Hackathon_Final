"""Builds one identical set of routes per provider.

Called once per provider (see bkash.py/nagad.py/rocket.py) with that
provider's own `get_db` dependency closed over - the resulting router can
only ever resolve a session bound to that provider's engine, so isolation is
structural, not just a convention the route bodies happen to follow.
"""

from datetime import datetime
from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app import services
from app.models import TransactionType
from app.schemas import BalanceOut, TransactionOut


def build_provider_router(provider: str, get_db: Callable[..., Session]) -> APIRouter:
    router = APIRouter(prefix=f"/{provider}", tags=[provider])

    @router.get("/provider/health")
    def health():
        return {"provider": provider, "status": "ok"}

    @router.get("/provider/balance/{agent_id}", response_model=BalanceOut)
    def get_balance(agent_id: str, session: Session = Depends(get_db)):
        balance = services.get_balance(session, agent_id)
        if not balance:
            raise HTTPException(404, f"No {provider} balance found for agent '{agent_id}'")
        return BalanceOut(
            provider=balance.provider,
            agent_id=balance.agent_id,
            balance=balance.emoney_balance,
            last_updated=balance.last_updated,
        )

    @router.get("/provider/transactions", response_model=list[TransactionOut])
    def get_transactions(
        agent_id: str,
        limit: int = Query(50, le=500),
        offset: int = Query(0, ge=0),
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None,
        session: Session = Depends(get_db),
    ):
        txs = services.list_transactions(
            session,
            agent_id=agent_id,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
        )
        return [
            TransactionOut(
                txn_id=t.txn_id,
                agent_id=t.agent_id,
                provider=t.provider,
                type=t.type,
                amount=t.amount,
                account_ref=t.account_ref,
                timestamp=t.timestamp,
            )
            for t in txs
        ]

    return router

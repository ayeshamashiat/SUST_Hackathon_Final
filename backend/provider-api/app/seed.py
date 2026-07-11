"""Reusable seed script for one provider database.

Generates a coherent transaction ledger (not just a random balance number):
starting from a random opening balance, transactions are created in
chronological order and each one moves a running balance the same way the
analytics layer (aggregator-api) expects a cash-out/cash-in to move e-money -
so the final `emoney_balance` is internally consistent with the transaction
history, not an unrelated number sitting next to it.

Idempotent: `seed_provider` is a no-op if that provider's database already
has balance rows, so re-running the app (or calling this again) never
duplicates or corrupts data.
"""

import random
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import select

from app.db import session_for
from app.models import Balance, Transaction, TransactionType
from app.seed_data import AGENTS, PROVIDER_OPENING_BALANCE_RANGE, PROVIDERS

TRANSACTIONS_PER_AGENT_RANGE = (20, 40)
HISTORY_HOURS = 72.0
AMOUNT_RANGE = (300.0, 5_000.0)
CASH_OUT_SHARE = 0.6  # cash-out (customer withdraws) dominates over cash-in, as in the live simulator


def is_seeded(provider: str) -> bool:
    with session_for(provider) as session:
        return session.exec(select(Balance)).first() is not None


def seed_provider(provider: str, now: Optional[datetime] = None) -> int:
    """Seeds one provider database with all agents' balances + transaction
    history. Returns the number of transactions created (0 if already
    seeded)."""
    now = now or datetime.utcnow()
    if is_seeded(provider):
        return 0

    created = 0
    with session_for(provider) as session:
        for agent_id, _name, _area in AGENTS:
            opening_balance = round(random.uniform(*PROVIDER_OPENING_BALANCE_RANGE[provider]), 2)
            running_balance = opening_balance

            tx_count = random.randint(*TRANSACTIONS_PER_AGENT_RANGE)
            # Oldest-first so running_balance reflects a coherent ledger.
            offsets_seconds = sorted((random.uniform(0, HISTORY_HOURS * 3600) for _ in range(tx_count)), reverse=True)

            for seconds_ago in offsets_seconds:
                is_cash_out = random.random() < CASH_OUT_SHARE
                amount = round(random.uniform(*AMOUNT_RANGE), 2)
                tx_type = TransactionType.CASH_OUT if is_cash_out else TransactionType.CASH_IN
                # CASH_OUT: customer sends e-money to receive physical cash ->
                # this agent's e-money balance increases. CASH_IN: reverse.
                # Mirrors the coupled cash/e-money model the analytics layer
                # (aggregator-api) relies on.
                running_balance += amount if is_cash_out else -amount
                session.add(
                    Transaction(
                        agent_id=agent_id,
                        provider=provider,
                        type=tx_type,
                        amount=amount,
                        account_ref=f"CUST-{random.randint(1000, 9999)}",
                        timestamp=now - timedelta(seconds=seconds_ago),
                        is_injected_anomaly=False,
                    )
                )
                created += 1

            session.add(
                Balance(
                    agent_id=agent_id,
                    provider=provider,
                    emoney_balance=round(running_balance, 2),
                    last_updated=now,
                )
            )
        session.commit()
    return created


def seed_all(now: Optional[datetime] = None) -> dict[str, int]:
    random.seed(42)  # reproducible demo data across fresh environments
    return {provider: seed_provider(provider, now=now) for provider in PROVIDERS}

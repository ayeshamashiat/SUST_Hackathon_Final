"""On-demand bulk historical data generator.

NOT run automatically on container startup - `seed.py`'s quick seed stays
fast for the normal dev loop. Run this explicitly when you want a deep,
realistic transaction history, e.g. to give aggregator-api's per-agent
historical anomaly baseline (services/anomaly.py's `detect_amount_outlier`)
something real to compare against, or to build a large enough labeled
dataset for Phase 7's offline precision/recall evaluation.

Usage (container already running):
    docker compose exec provider-api python -m app.historical_seed --days 90

Idempotent per agent+provider: skips backfilling any (agent, provider) pair
whose earliest transaction is already older than the requested window - so
re-running with the same --days is a no-op. Running with a LARGER --days
than a previous run correctly backfills just the additional gap. Extending
history never touches or duplicates transactions that already exist; it
only ever prepends further into the past, then adjusts the current balance
by the prequel's own net effect - the same running-ledger math seed.py and
the live simulator already use, just walked further back.
"""

import argparse
import random
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import select

from app.db import session_for
from app.models import Balance, Transaction, TransactionType
from app.seed_data import AGENTS, PROVIDER_OPENING_BALANCE_RANGE, PROVIDERS

AMOUNT_RANGE = (300.0, 5_000.0)
CASH_OUT_SHARE = 0.55
DAILY_TX_RANGE = (18, 45)  # base transactions/day per agent per provider
WEEKEND_MULTIPLIER = 1.4  # Bangladesh weekend (Fri/Sat) runs busier
BATCH_COMMIT_EVERY = 2_000  # rows per commit - keeps memory and lock time sane at this volume

# Hour-of-day weights (index 0-23): business hours get most of the volume,
# a long tail covers early morning / late night. Uniform-random timestamps
# read as obviously synthetic; this doesn't.
HOUR_WEIGHTS = (
    [0.2] * 6  # 00:00-05:59  quiet
    + [1.0] * 4  # 06:00-09:59  opening up
    + [2.2] * 10  # 10:00-19:59  core business hours
    + [1.2] * 2  # 20:00-21:59  evening wind-down
    + [0.4] * 2  # 22:00-23:59  late
)


def _pick_time_of_day() -> tuple[int, int, int]:
    hour = random.choices(range(24), weights=HOUR_WEIGHTS, k=1)[0]
    return hour, random.randint(0, 59), random.randint(0, 59)


def _daily_count(is_weekend: bool) -> int:
    count = random.randint(*DAILY_TX_RANGE)
    return round(count * WEEKEND_MULTIPLIER) if is_weekend else count


def _earliest_transaction_at(session, agent_id: str) -> Optional[datetime]:
    return session.exec(
        select(Transaction.timestamp).where(Transaction.agent_id == agent_id).order_by(Transaction.timestamp).limit(1)
    ).first()


def generate_provider_history(provider: str, days: int, now: Optional[datetime] = None) -> int:
    """Backfills history older than `days` ago, for every agent that doesn't
    already have it. Returns the number of transactions created."""
    now = now or datetime.utcnow()
    window_start = now - timedelta(days=days)
    created = 0

    with session_for(provider) as session:
        for agent_id, _name, _area in AGENTS:
            earliest = _earliest_transaction_at(session, agent_id)
            backfill_until = earliest if earliest is not None else now

            if backfill_until <= window_start:
                continue  # already has at least `days` of history for this agent+provider

            prequel_delta = 0.0
            day_cursor = window_start.replace(hour=0, minute=0, second=0, microsecond=0)
            while day_cursor < backfill_until:
                is_weekend = day_cursor.weekday() in (4, 5)  # Friday=4, Saturday=5
                for _ in range(_daily_count(is_weekend)):
                    h, m, s = _pick_time_of_day()
                    ts = day_cursor.replace(hour=h, minute=m, second=s)
                    if not (window_start <= ts < backfill_until):
                        continue

                    is_cash_out = random.random() < CASH_OUT_SHARE
                    amount = round(random.uniform(*AMOUNT_RANGE), 2)
                    tx_type = TransactionType.CASH_OUT if is_cash_out else TransactionType.CASH_IN
                    prequel_delta += amount if is_cash_out else -amount

                    session.add(
                        Transaction(
                            agent_id=agent_id,
                            provider=provider,
                            type=tx_type,
                            amount=amount,
                            account_ref=f"CUST-{random.randint(1000, 9999)}",
                            timestamp=ts,
                            is_injected_anomaly=False,
                        )
                    )
                    created += 1
                    if created % BATCH_COMMIT_EVERY == 0:
                        session.commit()

                day_cursor += timedelta(days=1)

            # Extend the SAME running ledger further into the past: the
            # current balance already reflects everything after
            # `backfill_until`, so it only needs to move by the prequel's
            # own net effect, not be recomputed from scratch.
            balance = session.get(Balance, agent_id)
            if balance is None:
                opening = round(random.uniform(*PROVIDER_OPENING_BALANCE_RANGE[provider]), 2)
                session.add(
                    Balance(
                        agent_id=agent_id,
                        provider=provider,
                        emoney_balance=round(opening + prequel_delta, 2),
                        last_updated=now,
                    )
                )
            else:
                balance.emoney_balance = round(balance.emoney_balance + prequel_delta, 2)
                session.add(balance)

        session.commit()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill deep historical transaction data across all providers.")
    parser.add_argument("--days", type=int, default=90, help="How many days of history to ensure exist (default 90).")
    args = parser.parse_args()

    now = datetime.utcnow()
    for provider in PROVIDERS:
        count = generate_provider_history(provider, args.days, now=now)
        note = "already had enough history - skipped" if count == 0 else f"{count} transactions created"
        print(f"{provider}: {note}")


if __name__ == "__main__":
    main()

"""Transaction generation for every simulator mode, plus the background tick
loop. Everything here writes into exactly one provider's own database via
`session_for(provider)` (see db.py) - the simulator never touches shared_db
or any other provider's data, matching Phase 3's scope (Provider API only).
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from app.db import session_for
from app.models import Balance, Transaction, TransactionType
from app.seed_data import AGENTS, PROVIDERS
from app.simulator.state import ScenarioState, state

TICK_SECONDS = 8.0
AGENT_IDS = [agent_id for agent_id, _, _ in AGENTS]

# --- mode tuning -----------------------------------------------------------

NORMAL_AMOUNT_RANGE = (300.0, 5_000.0)
NORMAL_CASH_OUT_SHARE = 0.55
# Chance a given agent+provider generates a tx this tick. Calibrated against
# this system's OWN definition of a realistic day (historical_seed.py's
# DAILY_TX_RANGE = 18-45/day/agent/provider): at TICK_SECONDS=8, a day is
# 10,800 ticks, and the NORMAL_HOUR_MULTIPLIER below averages ~0.854, so
# 0.0035 * 10,800 * 0.854 =~ 32/day - mid-range. The previous value (0.3)
# produced ~120 transactions/hour/agent/provider (measured directly against
# the running database) - about 100x too many for a single small outlet,
# and the main reason the derived cash balance kept drifting to unrealistic
# multi-million-taka deficits within a single day even after bounding the
# balance to a rolling window (see services/cash.py on the aggregator side).
NORMAL_TICK_PROBABILITY = 0.0035

EID_AMOUNT_RANGE = (500.0, 8_000.0)
EID_CASH_OUT_SHARE = 0.85  # Eid demand is dominated by customers withdrawing cash
EID_TICK_PROBABILITY = 0.8
EID_DEFAULT_COUNT_PER_AGENT = 5

# Hour-of-day multiplier for the ambient "normal" mode tick probability -
# mirrors historical_seed.py's HOUR_WEIGHTS shape so a full day of live
# simulation looks like the same realistic business-hours rhythm as the
# offline backfill, instead of a flat rate at every hour (uniform-random
# reads as obviously synthetic, and doesn't "simulate daily transactions"
# the way a real outlet actually behaves). Not applied to eid_spike mode,
# which is already an explicit, time-bounded demand scenario.
NORMAL_HOUR_MULTIPLIER = (
    [0.15] * 6  # 00:00-05:59  quiet
    + [0.6] * 4  # 06:00-09:59  opening up
    + [1.5] * 10  # 10:00-19:59  core business hours
    + [0.8] * 2  # 20:00-21:59  evening wind-down
    + [0.3] * 2  # 22:00-23:59  late
)


def _account_ref() -> str:
    """Wide, effectively-unique pool - the opposite of an anomaly burst's
    narrow repeating pool. This is what keeps a legitimate demand spike from
    resembling suspicious activity."""
    return f"CUST-{random.randint(10_000, 99_999)}"


def apply_transaction(
    provider: str,
    agent_id: str,
    tx_type: TransactionType,
    amount: float,
    account_ref: str,
    timestamp: Optional[datetime] = None,
    is_injected_anomaly: bool = False,
) -> Transaction:
    timestamp = timestamp or datetime.utcnow()
    with session_for(provider) as session:
        balance = session.get(Balance, agent_id)
        if balance is None:
            # Shouldn't happen once seeded, but don't silently drop the tx.
            balance = Balance(agent_id=agent_id, provider=provider, emoney_balance=0.0, last_updated=timestamp)

        # Same coupling seed.py uses: CASH_OUT credits this provider's
        # e-money balance (customer sends e-money to receive physical cash),
        # CASH_IN debits it.
        delta = amount if tx_type == TransactionType.CASH_OUT else -amount
        balance.emoney_balance = round(balance.emoney_balance + delta, 2)
        balance.last_updated = timestamp
        session.add(balance)

        tx = Transaction(
            agent_id=agent_id,
            provider=provider,
            type=tx_type,
            amount=amount,
            account_ref=account_ref,
            timestamp=timestamp,
            is_injected_anomaly=is_injected_anomaly,
        )
        session.add(tx)
        session.commit()
        session.refresh(tx)

    state.tx_counts[provider] += 1
    return tx


def generate_normal(provider: str, agent_id: str, count: int, now: Optional[datetime] = None) -> list[Transaction]:
    now = now or datetime.utcnow()
    created = []
    for _ in range(count):
        is_cash_out = random.random() < NORMAL_CASH_OUT_SHARE
        amount = round(random.uniform(*NORMAL_AMOUNT_RANGE), 2)
        created.append(
            apply_transaction(
                provider,
                agent_id,
                TransactionType.CASH_OUT if is_cash_out else TransactionType.CASH_IN,
                amount,
                _account_ref(),
                now - timedelta(seconds=random.uniform(0, 60)),
            )
        )
    return created


def generate_eid_spike(
    provider: str, agent_id: str, count: int, multiplier: float = 1.0, now: Optional[datetime] = None
) -> list[Transaction]:
    now = now or datetime.utcnow()
    scaled_count = max(1, round(count * multiplier))
    created = []
    for _ in range(scaled_count):
        is_cash_out = random.random() < EID_CASH_OUT_SHARE
        amount = round(random.uniform(*EID_AMOUNT_RANGE), 2)
        created.append(
            apply_transaction(
                provider,
                agent_id,
                TransactionType.CASH_OUT if is_cash_out else TransactionType.CASH_IN,
                amount,
                _account_ref(),  # wide, diverse pool - deliberately not anomaly-shaped
                now - timedelta(seconds=random.uniform(0, 60)),
            )
        )
    return created


def generate_anomaly_burst(
    provider: str,
    agent_id: str,
    count: int,
    window_seconds: float,
    amount: float,
    amount_jitter: float,
    account_pool_size: int,
    now: Optional[datetime] = None,
) -> list[Transaction]:
    """Near-identical amounts, a small repeating account pool, all within a
    tight time window - tagged `is_injected_anomaly=True` for Phase 7's
    offline precision/recall evaluation. Never exposed via any public
    endpoint (see schemas.py's TransactionOut)."""
    now = now or datetime.utcnow()
    account_pool = [f"CUST-{random.randint(1000, 9999)}" for _ in range(max(1, account_pool_size))]
    created = []
    for _ in range(count):
        amount_i = round(amount + random.uniform(-amount_jitter, amount_jitter), 2)
        ts = now - timedelta(seconds=random.uniform(0, window_seconds))
        created.append(
            apply_transaction(
                provider,
                agent_id,
                TransactionType.CASH_OUT,  # anomaly scenario in the brief is a cash-out burst
                amount_i,
                random.choice(account_pool),
                ts,
                is_injected_anomaly=True,
            )
        )
    state.last_anomaly_injected_at[provider] = now
    return created


def tick(now: Optional[datetime] = None) -> None:
    now = now or datetime.utcnow()
    state.last_tick_at = now

    if state.scenario.until and now >= state.scenario.until:
        state.scenario = ScenarioState()  # revert to normal once the scenario window ends

    active = state.scenario if (state.scenario.until and now < state.scenario.until) else None
    normal_probability = NORMAL_TICK_PROBABILITY * NORMAL_HOUR_MULTIPLIER[now.hour]

    for provider in PROVIDERS:
        if provider in state.paused_providers:
            continue  # simulated feed delay/break - this provider gets no new activity
        for agent_id in AGENT_IDS:
            if active and active.mode == "eid_spike":
                if random.random() < EID_TICK_PROBABILITY:
                    generate_eid_spike(provider, agent_id, count=1, multiplier=active.multiplier, now=now)
            else:
                if random.random() < normal_probability:
                    generate_normal(provider, agent_id, count=1, now=now)


async def _loop() -> None:
    while state.running:
        try:
            await asyncio.to_thread(tick)
        except Exception:
            # A single bad tick must never permanently kill the background
            # loop - found this exact failure mode in sync-service's loop
            # (an uncaught exception silently stopped it forever with
            # nothing in the logs); applying the same guard here as cheap
            # insurance against the identical pattern.
            logging.getLogger("provider-api.simulator").exception("tick() raised - will retry next interval")
        await asyncio.sleep(TICK_SECONDS)


_task: Optional[asyncio.Task] = None


def start() -> None:
    global _task
    if state.running:
        return
    state.running = True
    state.started_at = datetime.utcnow()
    _task = asyncio.create_task(_loop())


def stop() -> None:
    state.running = False

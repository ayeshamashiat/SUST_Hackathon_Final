"""Background transaction generator + feed-degradation controls.

The same generator code drives every demo scenario - agent "personality"
(which provider dominates, cash-in vs cash-out ratio, whether it gets
near-identical-amount bursts) lives entirely in ``profiles.py`` as data, not
as special-cased branches here.
"""

import asyncio
import random
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.alerts.engine import evaluate_agent
from app.core.config import TICK_SECONDS
from app.core.database import session_scope
from app.models.models import (
    CashDrawer,
    DataFeedStatus,
    FeedHealth,
    ProviderBalance,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from app.simulation.profiles import AGENT_PROFILES, AgentProfile, ProviderMix

_burst_counters: dict[str, int] = {}
_sim_start_time: Optional[datetime] = None
_task: Optional[asyncio.Task] = None
_running = False


def _weighted_choice(mix: list[ProviderMix]) -> str:
    total = sum(m.weight for m in mix)
    r = random.uniform(0, total)
    upto = 0.0
    for m in mix:
        upto += m.weight
        if r <= upto:
            return m.provider_id
    return mix[-1].provider_id


def _apply_transaction(
    session: Session,
    agent_id: str,
    provider_id: str,
    tx_type: TransactionType,
    amount: float,
    customer_ref: str,
    area: str,
    now: datetime,
    is_injected_anomaly: bool = False,
) -> Transaction:
    drawer = session.exec(select(CashDrawer).where(CashDrawer.agent_id == agent_id)).one()
    balance = session.exec(
        select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider_id == provider_id)
    ).one()

    # An agent cannot hand out cash it doesn't have, and cannot send e-money
    # it doesn't hold - a request that would overdraw fails outright rather
    # than pushing a balance negative. This is what a real shortage looks
    # like operationally (declined requests), not an unbounded overdraft.
    if tx_type == TransactionType.CASH_OUT:
        can_fulfill = drawer.balance >= amount
    else:
        can_fulfill = balance.balance >= amount

    tx = Transaction(
        agent_id=agent_id,
        provider_id=provider_id,
        type=tx_type,
        amount=amount,
        customer_ref=customer_ref,
        area=area,
        status=TransactionStatus.SUCCESS if can_fulfill else TransactionStatus.FAILED,
        is_injected_anomaly=is_injected_anomaly,
        created_at=now,
    )
    session.add(tx)

    if can_fulfill:
        if tx_type == TransactionType.CASH_OUT:
            drawer.balance -= amount
            balance.balance += amount
        else:
            drawer.balance += amount
            balance.balance -= amount
        drawer.updated_at = now
        balance.updated_at = now
        session.add(drawer)
        session.add(balance)

    # Feed freshness is a per-tick heartbeat (see tick()), not tied to
    # whether this specific transaction happened.
    session.commit()
    session.refresh(tx)
    return tx


def _maybe_fire_burst(session: Session, profile: AgentProfile, now: datetime) -> None:
    """Occasionally inject a burst of near-identical-amount cash-outs from a
    small customer pool, giving the velocity detector a real pattern to
    catch (illustrative Scenario B).

    Delayed by ``burst_start_after_minutes`` so the detector accumulates a
    clean, unburst baseline first - otherwise the "anomaly" would just be
    permanent background noise the detector normalizes against instead of a
    genuine deviation from normal.
    """
    if not profile.burst_enabled:
        return
    if _sim_start_time is not None:
        elapsed_minutes = (now - _sim_start_time).total_seconds() / 60.0
        if elapsed_minutes < profile.burst_start_after_minutes:
            return
    key = profile.agent_id
    if key not in _burst_counters:
        _burst_counters[key] = random.randint(*profile.burst_every_ticks_range)
    _burst_counters[key] -= 1
    if _burst_counters[key] > 0:
        return
    _burst_counters[key] = random.randint(*profile.burst_every_ticks_range)

    for _ in range(random.randint(*profile.burst_size_range)):
        amount = round(random.uniform(*profile.burst_amount_range), 2)
        customer = random.choice(profile.burst_customer_pool)
        _apply_transaction(
            session,
            profile.agent_id,
            profile.burst_provider,
            TransactionType.CASH_OUT,
            amount,
            customer,
            profile.area,
            now,
            is_injected_anomaly=True,
        )


def tick(now: Optional[datetime] = None) -> list[str]:
    """Advance the simulation by one tick and re-run alert evaluation for
    every agent that received new activity."""
    global _sim_start_time
    now = now or datetime.utcnow()
    if _sim_start_time is None:
        _sim_start_time = now
    touched_agents: set[str] = set()

    with session_scope() as session:
        for profile in AGENT_PROFILES.values():
            for _ in range(random.randint(*profile.tx_per_tick_range)):
                is_cash_out = random.random() < profile.cash_out_share
                mix = profile.cash_out_mix if is_cash_out else profile.cash_in_mix
                provider_id = _weighted_choice(mix)
                amount = round(random.uniform(*profile.amount_range), 2)
                customer = f"CUST-{random.randint(1000, 9999)}"
                _apply_transaction(
                    session,
                    profile.agent_id,
                    provider_id,
                    TransactionType.CASH_OUT if is_cash_out else TransactionType.CASH_IN,
                    amount,
                    customer,
                    profile.area,
                    now,
                )
                touched_agents.add(profile.agent_id)

            _maybe_fire_burst(session, profile, now)
            touched_agents.add(profile.agent_id)

        # A provider's balance feed heartbeats every tick regardless of
        # whether a transaction touched it - staleness should reflect an
        # actual (simulated) feed outage, not just low volume for a quiet
        # provider/agent pair.
        for feed in session.exec(select(DataFeedStatus)):
            if not feed.frozen:
                feed.last_update_at = now
                feed.health = FeedHealth.OK
                session.add(feed)
        session.commit()

        for agent_id in touched_agents:
            evaluate_agent(session, agent_id, now=now)

    return list(touched_agents)


def set_feed_frozen(agent_id: str, provider_id: str, frozen: bool, note: Optional[str] = None) -> None:
    with session_scope() as session:
        feed = session.exec(
            select(DataFeedStatus).where(DataFeedStatus.agent_id == agent_id, DataFeedStatus.provider_id == provider_id)
        ).one()
        feed.frozen = frozen
        feed.note = note
        if not frozen:
            feed.last_update_at = datetime.utcnow()
            feed.health = FeedHealth.OK
        session.add(feed)
        session.commit()


def reset() -> None:
    global _burst_counters, _sim_start_time
    _burst_counters = {}
    _sim_start_time = None
    with session_scope() as session:
        from app.simulation.seed import reset as reset_seed

        reset_seed(session)


async def _loop() -> None:
    global _running
    _running = True
    while _running:
        await asyncio.to_thread(tick)
        await asyncio.sleep(TICK_SECONDS)


def start() -> None:
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop())


def stop() -> None:
    global _running
    _running = False


def is_running() -> bool:
    return _running

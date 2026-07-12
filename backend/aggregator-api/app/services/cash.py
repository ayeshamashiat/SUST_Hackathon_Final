"""Derives the shared physical-cash balance for an agent - see config.py's
CASH_OPENING_BALANCE comment for why this is computed here instead of read
from a stored column: nothing in the system currently writes one.

The delta is summed over a rolling window (CASH_BALANCE_WINDOW_HOURS), not
all-time-since-epoch: a real outlet starts each day with a physical float
and gets it topped up/reconciled periodically - nothing in this system
models that replenishment event, so summing every transaction ever recorded
against one fixed opening balance drifts further from reality the longer
the simulator runs (found during Phase 3/4 verification: after ~90 days of
backfilled history, every agent's derived cash balance had drifted to
roughly -3.2M BDT, silently reported as "STABLE"). Bounding the window
keeps the figure representative of "cash on hand today" instead of an
unbounded cumulative ledger.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.config import CASH_BALANCE_WINDOW_HOURS, CASH_OPENING_BALANCE
from app.models import ProviderBalance, TransactionProjection
from app.services.confidence import ConfidenceLevel, provider_confidence, weakest

PROVIDERS = ("bkash", "nagad", "rocket")


def compute_cash_balance(
    session: Session, agent_id: str, now: Optional[datetime] = None
) -> tuple[float, dict[str, bool]]:
    """Returns the derived cash balance (summed over the last
    CASH_BALANCE_WINDOW_HOURS only) and, per provider, whether ANY
    transaction history at all has ever been seen (unbounded - False means
    that provider has never been synced for this agent, which is worse than
    "quiet today" and degrades confidence separately in evaluate_cash)."""
    now = now or datetime.utcnow()
    since = now - timedelta(hours=CASH_BALANCE_WINDOW_HOURS)

    recent_rows = list(
        session.exec(
            select(TransactionProjection).where(
                TransactionProjection.agent_id == agent_id,
                TransactionProjection.occurred_at >= since,
                TransactionProjection.occurred_at <= now,
            )
        )
    )
    delta = 0.0
    for tx in recent_rows:
        # CASH_OUT: agent hands physical cash to the customer -> cash drops.
        # CASH_IN: agent receives physical cash -> cash rises. Mirrors the
        # inverse convention already established for e-money in provider-api.
        delta += -tx.amount if tx.type == "cash_out" else tx.amount

    ever_seen: dict[str, bool] = {}
    for p in PROVIDERS:
        exists = session.exec(
            select(TransactionProjection.id)
            .where(TransactionProjection.agent_id == agent_id, TransactionProjection.provider == p)
            .limit(1)
        ).first()
        ever_seen[p] = exists is not None

    return CASH_OPENING_BALANCE + delta, ever_seen


def evaluate_cash(session: Session, agent_id: str) -> tuple[float, ConfidenceLevel, str]:
    """Cash aggregates all three providers, so its confidence can never be
    better than the least trustworthy provider feeding it - and a provider
    that's never been seen at all is worse than "missing," since the cash
    figure quietly excludes its effect rather than flagging a gap."""
    balance, seen_provider = compute_cash_balance(session, agent_id)

    provider_balances = {
        p: session.exec(
            select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == p)
        ).one_or_none()
        for p in PROVIDERS
    }

    confidences = []
    notes = []
    for p in PROVIDERS:
        if not seen_provider[p]:
            confidences.append(ConfidenceLevel.LOW)
            notes.append(f"{p}: no transaction history seen yet - cash figure may be understated.")
            continue
        level, note = provider_confidence(provider_balances[p])
        confidences.append(level)
        if level != ConfidenceLevel.HIGH:
            notes.append(f"{p}: {note}")

    return balance, weakest(*confidences), " ".join(notes)

"""Liquidity forecasting: EWMA-style burn-rate projection with an explicit,
sample-size-and-variance-based confidence rating.

Cash and provider e-money balances are treated as a coupled system, not
independent gauges: a CASH_OUT transaction drains the shared cash reserve
*and* fills the paying provider's e-money balance (and CASH_IN does the
reverse). ``_signed_delta`` encodes that coupling once, so every forecast -
cash or any single provider - is derived from the same transaction ledger.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import pstdev
from typing import Optional

from sqlmodel import Session, select

from app.core.config import (
    CASH_SAFETY_THRESHOLD,
    FORECAST_ALERT_HORIZON_MINUTES,
    FORECAST_HIGH_CONFIDENCE_SAMPLES,
    FORECAST_LOOKBACK_MINUTES,
    FORECAST_MIN_SAMPLES,
    FORECAST_MIN_WINDOW_MINUTES,
    PROVIDER_SAFETY_THRESHOLD,
    SIGNIFICANCE_Z_THRESHOLD,
)
from app.models.models import (
    CashDrawer,
    ConfidenceLevel,
    DataQuality,
    Provider,
    ProviderBalance,
    Transaction,
    TransactionStatus,
    TransactionType,
)


@dataclass
class ForecastResult:
    target: str  # "CASH" or a provider_id
    target_label: str
    status: str  # STABLE | AT_RISK | INSUFFICIENT_DATA
    current_balance: float
    burn_rate_per_minute: Optional[float] = None
    projected_shortage_at: Optional[datetime] = None
    minutes_to_shortage: Optional[float] = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_note: str = ""
    data_quality: DataQuality = DataQuality.OK
    top_contributors: list[dict] = field(default_factory=list)


def _signed_delta(tx: Transaction, target_is_cash: bool) -> float:
    if target_is_cash:
        return -tx.amount if tx.type == TransactionType.CASH_OUT else tx.amount
    return tx.amount if tx.type == TransactionType.CASH_OUT else -tx.amount


def forecast_cash(session: Session, agent_id: str, now: Optional[datetime] = None) -> ForecastResult:
    now = now or datetime.utcnow()
    drawer = session.exec(select(CashDrawer).where(CashDrawer.agent_id == agent_id)).one()
    txs = _recent_transactions(session, agent_id, provider_id=None, now=now)
    return _forecast(
        current_balance=drawer.balance,
        threshold=CASH_SAFETY_THRESHOLD,
        txs=txs,
        target="CASH",
        target_label="Shared Cash Reserve",
        target_is_cash=True,
        now=now,
    )


def forecast_provider(
    session: Session, agent_id: str, provider_id: str, now: Optional[datetime] = None
) -> ForecastResult:
    now = now or datetime.utcnow()
    bal = session.exec(
        select(ProviderBalance).where(
            ProviderBalance.agent_id == agent_id, ProviderBalance.provider_id == provider_id
        )
    ).one()
    provider = session.get(Provider, provider_id)
    txs = _recent_transactions(session, agent_id, provider_id=provider_id, now=now)
    return _forecast(
        current_balance=bal.balance,
        threshold=PROVIDER_SAFETY_THRESHOLD,
        txs=txs,
        target=provider_id,
        target_label=provider.name if provider else provider_id,
        target_is_cash=False,
        now=now,
    )


def _recent_transactions(
    session: Session, agent_id: str, provider_id: Optional[str], now: datetime
) -> list[Transaction]:
    since = now - timedelta(minutes=FORECAST_LOOKBACK_MINUTES)
    stmt = select(Transaction).where(
        Transaction.agent_id == agent_id,
        Transaction.created_at >= since,
        Transaction.status == TransactionStatus.SUCCESS,
    )
    if provider_id is not None:
        stmt = stmt.where(Transaction.provider_id == provider_id)
    return list(session.exec(stmt.order_by(Transaction.created_at)))


def _forecast(
    *,
    current_balance: float,
    threshold: float,
    txs: list[Transaction],
    target: str,
    target_label: str,
    target_is_cash: bool,
    now: datetime,
) -> ForecastResult:
    window_minutes = max((now - txs[0].created_at).total_seconds() / 60.0, 1.0) if txs else 0.0

    if len(txs) < FORECAST_MIN_SAMPLES or window_minutes < FORECAST_MIN_WINDOW_MINUTES:
        return ForecastResult(
            target=target,
            target_label=target_label,
            status="INSUFFICIENT_DATA",
            current_balance=current_balance,
            confidence=ConfidenceLevel.LOW,
            confidence_note=(
                f"Only {len(txs)} transaction(s) over {window_minutes:.1f} min observed - need at least "
                f"{FORECAST_MIN_SAMPLES} transactions across {FORECAST_MIN_WINDOW_MINUTES:.0f}+ min before "
                "projecting a trend, to avoid extrapolating from a few noisy seconds."
            ),
        )

    deltas = [_signed_delta(t, target_is_cash) for t in txs]
    n = len(deltas)
    mean_delta = sum(deltas) / n
    stdev_delta = pstdev(deltas) if n > 1 else 0.0
    standard_error = stdev_delta / (n**0.5) if n > 1 else 0.0
    # Two-sided z-like score for "is the mean per-transaction delta actually
    # below zero, or could this be noise around a flat trend?" - a standard
    # error significance test rather than a heuristic, so a burst of
    # consistent draining transactions is trusted quickly while a handful of
    # mixed-direction transactions is correctly treated as inconclusive.
    significance_z = abs(mean_delta) / standard_error if standard_error > 0 else float("inf")

    if mean_delta >= 0 or significance_z < SIGNIFICANCE_Z_THRESHOLD:
        return ForecastResult(
            target=target,
            target_label=target_label,
            status="STABLE",
            current_balance=current_balance,
            burn_rate_per_minute=sum(deltas) / window_minutes,
            confidence=ConfidenceLevel.MEDIUM if n >= FORECAST_HIGH_CONFIDENCE_SAMPLES else ConfidenceLevel.LOW,
            confidence_note=(
                "Balance is flat or growing based on recent activity."
                if mean_delta >= 0
                else "A slight downward drift was observed but is not statistically distinguishable from normal "
                "transaction-to-transaction noise yet."
            ),
        )

    rate_per_minute = sum(deltas) / window_minutes
    minutes_to_shortage = (current_balance - threshold) / abs(rate_per_minute)
    projected_at = now + timedelta(minutes=max(minutes_to_shortage, 0.0))

    if significance_z >= SIGNIFICANCE_Z_THRESHOLD * 2 and n >= FORECAST_HIGH_CONFIDENCE_SAMPLES:
        confidence = ConfidenceLevel.HIGH
        confidence_note = f"Based on {n} consistently declining transactions over the last {window_minutes:.0f} min (z={significance_z:.1f})."
    elif significance_z >= SIGNIFICANCE_Z_THRESHOLD * 2 or n >= FORECAST_HIGH_CONFIDENCE_SAMPLES:
        confidence = ConfidenceLevel.MEDIUM
        confidence_note = f"Based on {n} transactions over the last {window_minutes:.0f} min; treat the ETA as approximate."
    else:
        confidence = ConfidenceLevel.MEDIUM
        confidence_note = f"Statistically distinguishable downward trend (z={significance_z:.1f}), but based on limited data - treat the ETA as an early warning."

    status = "AT_RISK" if minutes_to_shortage <= FORECAST_ALERT_HORIZON_MINUTES else "STABLE"

    return ForecastResult(
        target=target,
        target_label=target_label,
        status=status,
        current_balance=current_balance,
        burn_rate_per_minute=rate_per_minute,
        projected_shortage_at=projected_at,
        minutes_to_shortage=minutes_to_shortage,
        confidence=confidence,
        confidence_note=confidence_note,
        top_contributors=_top_contributors(txs, target_is_cash),
    )


def _top_contributors(txs: list[Transaction], target_is_cash: bool) -> list[dict]:
    """Which provider is driving a CASH shortage - lets an alert say 'mostly bKash'."""
    if not target_is_cash:
        return []
    totals: dict[str, float] = {}
    for t in txs:
        delta = _signed_delta(t, target_is_cash=True)
        if delta < 0:
            totals[t.provider_id] = totals.get(t.provider_id, 0.0) + abs(delta)
    total_drain = sum(totals.values())
    if total_drain <= 0:
        return []
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return [{"provider_id": pid, "amount": amt, "share": round(amt / total_drain, 3)} for pid, amt in ranked]

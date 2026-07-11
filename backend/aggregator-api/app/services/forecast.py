"""Liquidity forecasting: burn-rate projection with an explicit,
sample-size-and-variance-based confidence rating, combined with the
data-quality confidence from services/confidence.py.

Ported from the earlier single-service prototype's analytics/forecaster.py
(same statistical approach, proven and already documented there) and
adapted to read from shared_db's transaction projection instead of a local
transaction table. Cash and provider e-money balances are treated as a
coupled system: a CASH_OUT drains cash and fills the paying provider's
e-money balance, CASH_IN the reverse - the same coupling services/cash.py
and provider-api's simulator already use, applied consistently here.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import pstdev
from typing import Optional

from sqlmodel import Session, select

from app.config import (
    CASH_SAFETY_THRESHOLD,
    FORECAST_ALERT_HORIZON_MINUTES,
    FORECAST_HIGH_CONFIDENCE_SAMPLES,
    FORECAST_LOOKBACK_MINUTES,
    FORECAST_MIN_SAMPLES,
    FORECAST_MIN_WINDOW_MINUTES,
    PROVIDER_SAFETY_THRESHOLD,
    SIGNIFICANCE_Z_THRESHOLD,
)
from app.models import ProviderBalance, TransactionProjection
from app.services.cash import evaluate_cash
from app.services.confidence import ConfidenceLevel, provider_confidence, weakest


@dataclass
class ForecastResult:
    target: str  # "CASH" or a provider id
    target_label: str
    status: str  # STABLE | AT_RISK | INSUFFICIENT_DATA
    current_balance: float
    burn_rate_per_minute: Optional[float] = None
    projected_shortage_at: Optional[datetime] = None
    minutes_to_shortage: Optional[float] = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_note: str = ""
    top_contributors: list[dict] = field(default_factory=list)


def _signed_delta(tx: TransactionProjection, target_is_cash: bool) -> float:
    if target_is_cash:
        return -tx.amount if tx.type == "cash_out" else tx.amount
    return tx.amount if tx.type == "cash_out" else -tx.amount


def _recent_transactions(
    session: Session, agent_id: str, provider: Optional[str], now: datetime
) -> list[TransactionProjection]:
    since = now - timedelta(minutes=FORECAST_LOOKBACK_MINUTES)
    stmt = select(TransactionProjection).where(
        TransactionProjection.agent_id == agent_id, TransactionProjection.occurred_at >= since
    )
    if provider is not None:
        stmt = stmt.where(TransactionProjection.provider == provider)
    return list(session.exec(stmt.order_by(TransactionProjection.occurred_at)))


def forecast_cash(session: Session, agent_id: str, now: Optional[datetime] = None) -> ForecastResult:
    now = now or datetime.utcnow()
    current_balance, data_quality_confidence, data_quality_note = evaluate_cash(session, agent_id)
    txs = _recent_transactions(session, agent_id, provider=None, now=now)

    result = _forecast(
        current_balance=current_balance,
        threshold=CASH_SAFETY_THRESHOLD,
        txs=txs,
        target="CASH",
        target_label="Shared Cash Reserve",
        target_is_cash=True,
        now=now,
    )
    _apply_data_quality_ceiling(result, data_quality_confidence, [data_quality_note] if data_quality_note else [])
    return result


def forecast_provider(session: Session, agent_id: str, provider: str, now: Optional[datetime] = None) -> ForecastResult:
    now = now or datetime.utcnow()
    balance = session.exec(
        select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == provider)
    ).one_or_none()

    if balance is None:
        return ForecastResult(
            target=provider,
            target_label=provider,
            status="INSUFFICIENT_DATA",
            current_balance=0.0,
            confidence=ConfidenceLevel.LOW,
            confidence_note="No synced balance for this provider yet - this agent may not be registered with it, "
            "or it has never successfully synced. Treat as missing, not zero.",
        )

    txs = _recent_transactions(session, agent_id, provider=provider, now=now)
    result = _forecast(
        current_balance=balance.emoney_balance,
        threshold=PROVIDER_SAFETY_THRESHOLD,
        txs=txs,
        target=provider,
        target_label=provider,
        target_is_cash=False,
        now=now,
    )
    data_quality_confidence, data_quality_note = provider_confidence(balance)
    _apply_data_quality_ceiling(result, data_quality_confidence, [data_quality_note] if data_quality_note else [])
    return result


def _apply_data_quality_ceiling(result: ForecastResult, data_quality_confidence: ConfidenceLevel, notes: list[str]) -> None:
    """The statistical confidence from the transaction trend alone can't
    exceed what the underlying data's freshness/consistency supports - a
    perfectly clean-looking downward trend computed from stale or
    conflicting source data is not actually a HIGH-confidence result."""
    combined = weakest(result.confidence, data_quality_confidence)
    if combined != result.confidence:
        result.confidence = combined
    if notes:
        result.confidence_note = (result.confidence_note + " " if result.confidence_note else "") + " ".join(notes)


def _forecast(
    *,
    current_balance: float,
    threshold: float,
    txs: list[TransactionProjection],
    target: str,
    target_label: str,
    target_is_cash: bool,
    now: datetime,
) -> ForecastResult:
    window_minutes = max((now - txs[0].occurred_at).total_seconds() / 60.0, 1.0) if txs else 0.0

    if len(txs) < FORECAST_MIN_SAMPLES or window_minutes < FORECAST_MIN_WINDOW_MINUTES:
        return ForecastResult(
            target=target,
            target_label=target_label,
            status="INSUFFICIENT_DATA",
            current_balance=current_balance,
            confidence=ConfidenceLevel.LOW,
            confidence_note=(
                f"Only {len(txs)} transaction(s) over {window_minutes:.1f} min observed - need at least "
                f"{FORECAST_MIN_SAMPLES} across {FORECAST_MIN_WINDOW_MINUTES:.0f}+ min before projecting a trend."
            ),
        )

    deltas = [_signed_delta(t, target_is_cash) for t in txs]
    n = len(deltas)
    mean_delta = sum(deltas) / n
    stdev_delta = pstdev(deltas) if n > 1 else 0.0
    standard_error = stdev_delta / (n**0.5) if n > 1 else 0.0
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
        confidence_note = (
            f"Statistically distinguishable downward trend (z={significance_z:.1f}), but based on limited data - "
            "treat the ETA as an early warning."
        )

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


def _top_contributors(txs: list[TransactionProjection], target_is_cash: bool) -> list[dict]:
    """Which provider is driving a cash shortage - lets a forecast say
    'mostly bKash' instead of just a bare number."""
    if not target_is_cash:
        return []
    totals: dict[str, float] = {}
    for t in txs:
        delta = _signed_delta(t, target_is_cash=True)
        if delta < 0:
            totals[t.provider] = totals.get(t.provider, 0.0) + abs(delta)
    total_drain = sum(totals.values())
    if total_drain <= 0:
        return []
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return [{"provider": p, "amount": amt, "share": round(amt / total_drain, 3)} for p, amt in ranked]

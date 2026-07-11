"""Velocity-spike anomaly detection: is the recent cash-out rate for a
provider statistically unusual compared to this agent's own recent baseline?

Deliberately simple and explainable (rolling counts + z-score) rather than a
black-box model, so every flag can show its exact evidence and threshold.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import pstdev
from typing import Optional

from sqlmodel import Session, select

from app.core.config import (
    VELOCITY_BASELINE_MINUTES,
    VELOCITY_MIN_BASELINE_COUNT,
    VELOCITY_MIN_HISTORY_MINUTES,
    VELOCITY_MIN_WINDOW_COUNT,
    VELOCITY_WINDOW_MINUTES,
    VELOCITY_Z_SCORE_THRESHOLD,
)
from app.models.models import ConfidenceLevel, Transaction, TransactionStatus, TransactionType


@dataclass
class AnomalyResult:
    provider_id: str
    flagged: bool
    window_count: int
    baseline_mean: float
    baseline_stdev: float
    z_score: Optional[float]
    unique_customers: int
    amount_min: float
    amount_max: float
    sample_transaction_ids: list[int] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_note: str = ""


def detect_velocity_spike(
    session: Session, agent_id: str, provider_id: str, now: Optional[datetime] = None
) -> AnomalyResult:
    now = now or datetime.utcnow()
    window_start = now - timedelta(minutes=VELOCITY_WINDOW_MINUTES)
    baseline_start = now - timedelta(minutes=VELOCITY_BASELINE_MINUTES)

    window_txs = _cash_out_txs(session, agent_id, provider_id, window_start, now)
    baseline_txs = _cash_out_txs(session, agent_id, provider_id, baseline_start, window_start)

    # Clamp the baseline to when data actually starts - otherwise a young
    # agent's "pre-existence" period reads as many empty buckets and makes
    # any normal window count look like a huge spike.
    earliest_known = baseline_txs[0].created_at if baseline_txs else (window_txs[0].created_at if window_txs else None)
    effective_baseline_start = max(baseline_start, earliest_known) if earliest_known else baseline_start
    history_minutes = max((window_start - effective_baseline_start).total_seconds() / 60.0, 0.0) if earliest_known else 0.0

    window_count = len(window_txs)
    bucket_counts = _bucket_counts(baseline_txs, effective_baseline_start, window_start, VELOCITY_WINDOW_MINUTES)
    baseline_mean = sum(bucket_counts) / len(bucket_counts) if bucket_counts else 0.0
    baseline_stdev = pstdev(bucket_counts) if len(bucket_counts) > 1 else 0.0

    z_score: Optional[float] = None
    if bucket_counts and baseline_stdev > 0:
        z_score = (window_count - baseline_mean) / baseline_stdev

    has_mature_baseline = len(baseline_txs) >= VELOCITY_MIN_BASELINE_COUNT and history_minutes >= VELOCITY_MIN_HISTORY_MINUTES

    flagged = bool(
        window_count >= VELOCITY_MIN_WINDOW_COUNT
        and has_mature_baseline
        and z_score is not None
        and z_score >= VELOCITY_Z_SCORE_THRESHOLD
    )

    if not has_mature_baseline:
        confidence = ConfidenceLevel.LOW
        confidence_note = (
            f"Only {history_minutes:.0f} min of observed history for this provider at this agent - "
            f"need at least {VELOCITY_MIN_HISTORY_MINUTES:.0f} min before reliably calling this unusual."
        )
    elif z_score is not None and z_score >= VELOCITY_Z_SCORE_THRESHOLD * 1.5:
        confidence = ConfidenceLevel.HIGH
        confidence_note = f"Window count is far above the recent baseline (z={z_score:.1f})."
    else:
        confidence = ConfidenceLevel.MEDIUM
        confidence_note = "Moderate deviation from this agent's recent baseline."

    amounts = [t.amount for t in window_txs] or [0.0]
    customers = {t.customer_ref for t in window_txs}

    return AnomalyResult(
        provider_id=provider_id,
        flagged=flagged,
        window_count=window_count,
        baseline_mean=baseline_mean,
        baseline_stdev=baseline_stdev,
        z_score=z_score,
        unique_customers=len(customers),
        amount_min=min(amounts),
        amount_max=max(amounts),
        sample_transaction_ids=[t.id for t in window_txs[:10] if t.id is not None],
        confidence=confidence,
        confidence_note=confidence_note,
    )


def _cash_out_txs(
    session: Session, agent_id: str, provider_id: str, start: datetime, end: datetime
) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .where(
            Transaction.agent_id == agent_id,
            Transaction.provider_id == provider_id,
            Transaction.type == TransactionType.CASH_OUT,
            Transaction.status == TransactionStatus.SUCCESS,
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        .order_by(Transaction.created_at)
    )
    return list(session.exec(stmt))


def _bucket_counts(txs: list[Transaction], start: datetime, end: datetime, bucket_minutes: float) -> list[int]:
    if end <= start:
        return []
    bucket = timedelta(minutes=bucket_minutes)
    buckets: list[int] = []
    cursor = start
    while cursor < end:
        nxt = min(cursor + bucket, end)
        buckets.append(sum(1 for t in txs if cursor <= t.created_at < nxt))
        cursor = nxt
    return buckets

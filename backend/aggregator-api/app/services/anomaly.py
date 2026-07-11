"""Explainable, rule-based cash-out anomaly detection - no black-box model.

Combines three signals, all computed directly from shared_db's transaction
projection so every flag can cite exact evidence:

  - rolling z-score:      is the recent cash-out COUNT unusual vs this
                          agent+provider's own recent baseline?
  - frequency analysis:   the window/baseline transaction counts themselves.
  - account clustering:   are those transactions concentrated in a handful
                          of repeating account_refs, or spread across many
                          distinct ones?

The z-score alone cannot tell a real Eid-style demand spike (high volume,
but spread across many distinct customers) apart from an injected/suspicious
burst (high volume AND concentrated in a few repeating accounts) - Phase 3's
`generate_eid_spike` is deliberately diverse for exactly this reason. Both
conditions are required together before anything is flagged, which is what
keeps a legitimate spike from reading as "unusual."

Language is deliberately advisory: "unusual", "requires review", confidence
levels - never "fraud" or "confirmed". This is a decision-support signal for
human review, not a determination.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import mean, pstdev
from typing import Optional

from sqlmodel import Session, select

from app.config import (
    ANOMALY_BASELINE_MINUTES,
    ANOMALY_CONCENTRATION_THRESHOLD,
    ANOMALY_MIN_BASELINE_COUNT,
    ANOMALY_MIN_HISTORY_MINUTES,
    ANOMALY_MIN_WINDOW_COUNT,
    ANOMALY_WINDOW_MINUTES,
    ANOMALY_Z_THRESHOLD,
    HISTORICAL_LOOKBACK_DAYS,
    HISTORICAL_MIN_SAMPLES,
    HISTORICAL_Z_THRESHOLD,
)
from app.models import TransactionProjection
from app.services.confidence import ConfidenceLevel


@dataclass
class AnomalyResult:
    agent_id: str
    provider: str
    flagged: bool
    window_count: int
    baseline_mean: float
    baseline_stdev: float
    z_score: Optional[float]
    unique_customers: int
    concentration_ratio: Optional[float]  # unique_customers / window_count; lower = more repeated accounts
    amount_min: float
    amount_max: float
    amount_coefficient_of_variation: Optional[float]  # lower = amounts are closer to identical
    sample_transaction_ids: list[int] = field(default_factory=list)
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    message: str = ""


def _cash_out_txs(session: Session, agent_id: str, provider: str, start: datetime, end: datetime) -> list[TransactionProjection]:
    stmt = (
        select(TransactionProjection)
        .where(
            TransactionProjection.agent_id == agent_id,
            TransactionProjection.provider == provider,
            TransactionProjection.type == "cash_out",
            TransactionProjection.occurred_at >= start,
            TransactionProjection.occurred_at < end,
        )
        .order_by(TransactionProjection.occurred_at)
    )
    return list(session.exec(stmt))


def _bucket_counts(txs: list[TransactionProjection], start: datetime, end: datetime, bucket_minutes: float) -> list[int]:
    if end <= start:
        return []
    bucket = timedelta(minutes=bucket_minutes)
    counts: list[int] = []
    cursor = start
    while cursor < end:
        nxt = min(cursor + bucket, end)
        counts.append(sum(1 for t in txs if cursor <= t.occurred_at < nxt))
        cursor = nxt
    return counts


def detect_velocity_and_clustering(
    session: Session, agent_id: str, provider: str, now: Optional[datetime] = None
) -> AnomalyResult:
    now = now or datetime.utcnow()
    window_start = now - timedelta(minutes=ANOMALY_WINDOW_MINUTES)
    baseline_start = now - timedelta(minutes=ANOMALY_BASELINE_MINUTES)

    window_txs = _cash_out_txs(session, agent_id, provider, window_start, now)
    baseline_txs = _cash_out_txs(session, agent_id, provider, baseline_start, window_start)

    earliest_known = baseline_txs[0].occurred_at if baseline_txs else (window_txs[0].occurred_at if window_txs else None)
    effective_baseline_start = max(baseline_start, earliest_known) if earliest_known else baseline_start
    history_minutes = (
        max((window_start - effective_baseline_start).total_seconds() / 60.0, 0.0) if earliest_known else 0.0
    )

    window_count = len(window_txs)
    bucket_counts = _bucket_counts(baseline_txs, effective_baseline_start, window_start, ANOMALY_WINDOW_MINUTES)
    baseline_mean = sum(bucket_counts) / len(bucket_counts) if bucket_counts else 0.0
    baseline_stdev = pstdev(bucket_counts) if len(bucket_counts) > 1 else 0.0

    z_score: Optional[float] = None
    if bucket_counts and baseline_stdev > 0:
        z_score = (window_count - baseline_mean) / baseline_stdev

    has_mature_baseline = len(baseline_txs) >= ANOMALY_MIN_BASELINE_COUNT and history_minutes >= ANOMALY_MIN_HISTORY_MINUTES

    unique_customers = len({t.account_ref for t in window_txs})
    concentration_ratio = (unique_customers / window_count) if window_count > 0 else None

    amounts = [t.amount for t in window_txs]
    amount_cv = (pstdev(amounts) / mean(amounts)) if len(amounts) > 1 and mean(amounts) > 0 else None

    is_frequency_anomalous = (
        window_count >= ANOMALY_MIN_WINDOW_COUNT
        and has_mature_baseline
        and z_score is not None
        and z_score >= ANOMALY_Z_THRESHOLD
    )
    is_concentrated = concentration_ratio is not None and concentration_ratio <= ANOMALY_CONCENTRATION_THRESHOLD
    flagged = bool(is_frequency_anomalous and is_concentrated)

    if not has_mature_baseline:
        confidence = ConfidenceLevel.LOW
    elif flagged and z_score is not None and z_score >= ANOMALY_Z_THRESHOLD * 1.5 and (concentration_ratio or 1) <= 0.3:
        confidence = ConfidenceLevel.HIGH
    elif flagged:
        confidence = ConfidenceLevel.MEDIUM
    else:
        confidence = ConfidenceLevel.MEDIUM if is_frequency_anomalous or is_concentrated else ConfidenceLevel.LOW

    message = _build_message(
        provider, window_count, unique_customers, concentration_ratio, z_score, amount_cv, flagged, has_mature_baseline
    )

    return AnomalyResult(
        agent_id=agent_id,
        provider=provider,
        flagged=flagged,
        window_count=window_count,
        baseline_mean=baseline_mean,
        baseline_stdev=baseline_stdev,
        z_score=z_score,
        unique_customers=unique_customers,
        concentration_ratio=concentration_ratio,
        amount_min=min(amounts) if amounts else 0.0,
        amount_max=max(amounts) if amounts else 0.0,
        amount_coefficient_of_variation=amount_cv,
        sample_transaction_ids=[t.provider_txn_id for t in window_txs[:10]],
        window_start=window_start,
        window_end=now,
        confidence=confidence,
        message=message,
    )


def _build_message(
    provider: str,
    window_count: int,
    unique_customers: int,
    concentration_ratio: Optional[float],
    z_score: Optional[float],
    amount_cv: Optional[float],
    flagged: bool,
    has_mature_baseline: bool,
) -> str:
    if not has_mature_baseline:
        return (
            f"Not enough observed history for {provider} at this agent yet to judge whether recent activity is "
            "unusual - low confidence either way."
        )
    if not flagged:
        return f"Recent {provider} cash-out activity is within the agent's normal pattern - no review needed."

    z_part = f"z={z_score:.1f}" if z_score is not None else "z=n/a"
    concentration_part = f"{unique_customers} account(s) for {window_count} transactions"
    amount_part = f", amounts are close to identical (CV={amount_cv:.2f})" if amount_cv is not None and amount_cv < 0.05 else ""
    return (
        f"Unusual {provider} cash-out activity requires review: {window_count} transactions in a short window "
        f"({z_part} vs. this agent's baseline), concentrated in only {concentration_part}{amount_part}. "
        "This may be normal demand or a data artifact, but it should be reviewed before approving a large "
        "cash replenishment. This is not a fraud determination."
    )


@dataclass
class AmountOutlierResult:
    """Answers a different question than AnomalyResult above: not 'is there
    a burst of activity' but 'is this agent's most recent transaction an
    unusual AMOUNT for what this specific agent normally does' - evaluated
    against that one agent's own historical distribution, not a fleet-wide
    or generic threshold. Requires HISTORICAL_LOOKBACK_DAYS of real history
    to mean anything (see provider-api/app/historical_seed.py)."""

    agent_id: str
    provider: str
    transaction_type: str
    flagged: bool
    evaluated_transaction_id: Optional[int]
    evaluated_amount: Optional[float]
    evaluated_at: Optional[datetime]
    historical_sample_size: int
    historical_mean: Optional[float]
    historical_stdev: Optional[float]
    z_score: Optional[float]
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    message: str = ""


def detect_amount_outlier(
    session: Session,
    agent_id: str,
    provider: str,
    transaction_type: str = "cash_out",
    lookback_days: float = HISTORICAL_LOOKBACK_DAYS,
    now: Optional[datetime] = None,
) -> AmountOutlierResult:
    now = now or datetime.utcnow()
    since = now - timedelta(days=lookback_days)

    txs = list(
        session.exec(
            select(TransactionProjection)
            .where(
                TransactionProjection.agent_id == agent_id,
                TransactionProjection.provider == provider,
                TransactionProjection.type == transaction_type,
                TransactionProjection.occurred_at >= since,
                TransactionProjection.occurred_at <= now,
            )
            .order_by(TransactionProjection.occurred_at)
        )
    )

    if len(txs) < HISTORICAL_MIN_SAMPLES + 1:
        return AmountOutlierResult(
            agent_id=agent_id,
            provider=provider,
            transaction_type=transaction_type,
            flagged=False,
            evaluated_transaction_id=txs[-1].provider_txn_id if txs else None,
            evaluated_amount=txs[-1].amount if txs else None,
            evaluated_at=txs[-1].occurred_at if txs else None,
            historical_sample_size=max(len(txs) - 1, 0),
            historical_mean=None,
            historical_stdev=None,
            z_score=None,
            confidence=ConfidenceLevel.LOW,
            message=(
                f"Only {len(txs)} {transaction_type} transaction(s) in the last {lookback_days:.0f} days for this "
                f"agent+provider - need at least {HISTORICAL_MIN_SAMPLES + 1} before 'unusual for this agent' is a "
                "meaningful statement. Run provider-api's historical_seed to backfill more history."
            ),
        )

    # Evaluate the most recent transaction against everything before it -
    # "was this specific transaction unusual, given what this agent had
    # already done up to that point" rather than including it in its own
    # baseline.
    *history, latest = txs
    amounts = [t.amount for t in history]
    hist_mean = mean(amounts)
    hist_stdev = pstdev(amounts) if len(amounts) > 1 else 0.0

    z_score = (latest.amount - hist_mean) / hist_stdev if hist_stdev > 0 else None
    flagged = z_score is not None and z_score >= HISTORICAL_Z_THRESHOLD

    if z_score is not None and z_score >= HISTORICAL_Z_THRESHOLD * 1.5:
        confidence = ConfidenceLevel.HIGH
    elif flagged:
        confidence = ConfidenceLevel.MEDIUM
    else:
        confidence = ConfidenceLevel.MEDIUM if len(history) >= HISTORICAL_MIN_SAMPLES * 2 else ConfidenceLevel.LOW

    if flagged:
        message = (
            f"This agent's most recent {provider} {transaction_type.replace('_', '-')} was {latest.amount:.0f} BDT, "
            f"unusual for this specific agent - their typical {transaction_type.replace('_', '-')} over the last "
            f"{lookback_days:.0f} days averages {hist_mean:.0f} BDT (z={z_score:.1f} vs. their own history, "
            f"{len(history)} prior transactions). This may be a legitimate large transaction, but it should be "
            "reviewed before acting on it. This is not a fraud determination."
        )
    else:
        message = (
            f"This agent's most recent {provider} {transaction_type.replace('_', '-')} ({latest.amount:.0f} BDT) is "
            f"consistent with their own historical pattern (avg {hist_mean:.0f} BDT over {len(history)} prior "
            "transactions) - no review needed on this basis."
        )

    return AmountOutlierResult(
        agent_id=agent_id,
        provider=provider,
        transaction_type=transaction_type,
        flagged=flagged,
        evaluated_transaction_id=latest.provider_txn_id,
        evaluated_amount=latest.amount,
        evaluated_at=latest.occurred_at,
        historical_sample_size=len(history),
        historical_mean=hist_mean,
        historical_stdev=hist_stdev,
        z_score=z_score,
        confidence=confidence,
        message=message,
    )

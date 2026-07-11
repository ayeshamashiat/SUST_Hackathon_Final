from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.auth.deps import get_current_user
from app.auth.models import User, UserRole
from app.config import CASH_OPENING_BALANCE
from app.db import get_shared_db
from app.models import ProviderBalance, TransactionProjection
from app.schemas import (
    AgentAggregateOut,
    AmountOutlierOut,
    AnomalyOut,
    CashTrendPointOut,
    ForecastOut,
    ProviderBalanceOut,
    TransactionOut,
)
from app.services import anomaly as anomaly_service
from app.services import forecast as forecast_service
from app.services.cash import PROVIDERS, evaluate_cash
from app.services.confidence import provider_confidence, weakest

router = APIRouter(prefix="/aggregate", tags=["aggregate"])


def _require_agent_scope(user: User, agent_id: str) -> None:
    """AGENT-role logins only ever see their own outlet - never another
    agent's balances, forecast, or anomaly evidence."""
    if user.role == UserRole.AGENT and agent_id != user.agent_id:
        raise HTTPException(403, "Not authorized to view this agent")


def _scoped_providers(user: User, requested: list[str]) -> list[str]:
    """PROVIDER_OPS-role logins only ever see their own provider's data -
    a bKash ops login cannot pull Nagad's forecast or anomaly evidence
    through this API, mirroring the database-level boundary enforced
    between provider-api's own routers."""
    if user.role != UserRole.PROVIDER_OPS:
        return requested
    if user.provider_id not in requested:
        raise HTTPException(403, "Not authorized to view this provider")
    return [user.provider_id]


@router.get("/agent/{agent_id}", response_model=AgentAggregateOut)
def get_agent_aggregate(
    agent_id: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_shared_db)
):
    _require_agent_scope(current_user, agent_id)
    cash_balance, cash_confidence, cash_note = evaluate_cash(session, agent_id)

    provider_rows = {
        p: session.exec(
            select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == p)
        ).one_or_none()
        for p in PROVIDERS
    }

    if all(row is None for row in provider_rows.values()):
        raise HTTPException(404, f"Agent '{agent_id}' not found - no provider has ever synced data for it")

    visible_providers = _scoped_providers(current_user, list(PROVIDERS))
    providers_out = []
    confidences = [cash_confidence]
    for p in visible_providers:
        row = provider_rows[p]
        level, note = provider_confidence(row)
        confidences.append(level)
        providers_out.append(
            ProviderBalanceOut(
                provider=p,
                balance=row.emoney_balance if row else None,
                staleness_seconds=row.staleness_seconds if row else None,
                sync_status=row.sync_status.value if row else None,
                confidence=level,
                confidence_note=note,
            )
        )

    return AgentAggregateOut(
        agent_id=agent_id,
        cash_balance=round(cash_balance, 2),
        cash_confidence=cash_confidence,
        cash_confidence_note=cash_note or "Recently synced and internally consistent across all providers.",
        providers=providers_out,
        overall_confidence=weakest(*confidences),
    )


@router.get("/transactions/{agent_id}", response_model=list[TransactionOut])
def get_agent_transactions(
    agent_id: str,
    provider: str = Query(None, description="Limit to one provider (bkash/nagad/rocket); omit for all three."),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_shared_db),
):
    """Recent cash-in/cash-out stream for the dashboard - reads the
    cross-provider transactions_projection mirror directly rather than
    fanning out to provider-api, same as every other route in this file."""
    _require_agent_scope(current_user, agent_id)
    requested = [provider] if provider else list(PROVIDERS)
    unknown = set(requested) - set(PROVIDERS)
    if unknown:
        raise HTTPException(400, f"Unknown provider(s): {sorted(unknown)}. Valid: {list(PROVIDERS)}")
    providers = _scoped_providers(current_user, requested)

    rows = session.exec(
        select(TransactionProjection)
        .where(TransactionProjection.agent_id == agent_id, TransactionProjection.provider.in_(providers))
        .order_by(TransactionProjection.occurred_at.desc())
        .limit(limit)
    ).all()

    return [
        TransactionOut(
            id=row.id,
            agent_id=row.agent_id,
            provider=row.provider,
            type=row.type,
            amount=row.amount,
            account_ref=row.account_ref,
            occurred_at=row.occurred_at,
        )
        for row in rows
    ]


@router.get("/cash-trend/{agent_id}", response_model=list[CashTrendPointOut])
def get_agent_cash_trend(
    agent_id: str,
    hours: int = Query(12, ge=1, le=48, description="How many hours of history to bucket, ending now."),
    buckets: int = Query(12, ge=2, le=48, description="Number of equal-width buckets across the window."),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_shared_db),
):
    """Reconstructs the shared cash-reserve balance over time by replaying
    transactions_projection deltas bucket by bucket, the same signed-amount
    convention as services/cash.py - there's no stored balance history, so
    this is derived fresh from the same source of truth on every call."""
    _require_agent_scope(current_user, agent_id)

    rows = list(
        session.exec(
            select(TransactionProjection)
            .where(TransactionProjection.agent_id == agent_id)
            .order_by(TransactionProjection.occurred_at.asc())
        )
    )
    if not rows:
        raise HTTPException(404, f"Agent '{agent_id}' not found - no provider has ever synced data for it")

    window_end = rows[-1].occurred_at
    window_start = window_end - timedelta(hours=hours)
    bucket_width = (window_end - window_start) / buckets

    # Balance carried in from before the window, so the first bucket's
    # cash_balance reflects everything that happened prior to it.
    balance = CASH_OPENING_BALANCE
    for row in rows:
        if row.occurred_at >= window_start:
            break
        balance += -row.amount if row.type == "cash_out" else row.amount

    points: list[CashTrendPointOut] = []
    row_idx = 0
    for i in range(buckets):
        bucket_start = window_start + bucket_width * i
        bucket_end = bucket_start + bucket_width
        cash_in = 0.0
        cash_out = 0.0
        while row_idx < len(rows) and rows[row_idx].occurred_at < bucket_end:
            row = rows[row_idx]
            if row.occurred_at >= bucket_start:
                if row.type == "cash_out":
                    cash_out += row.amount
                    balance -= row.amount
                else:
                    cash_in += row.amount
                    balance += row.amount
            row_idx += 1
        points.append(
            CashTrendPointOut(
                bucket_start=bucket_start,
                bucket_end=bucket_end,
                cash_balance=round(balance, 2),
                cash_in=round(cash_in, 2),
                cash_out=round(cash_out, 2),
            )
        )

    return points


@router.get("/forecast/{agent_id}", response_model=list[ForecastOut])
def get_agent_forecast(
    agent_id: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_shared_db)
):
    _require_agent_scope(current_user, agent_id)
    exists = any(
        session.exec(
            select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == p)
        ).one_or_none()
        for p in PROVIDERS
    )
    if not exists:
        raise HTTPException(404, f"Agent '{agent_id}' not found - no provider has ever synced data for it")

    visible_providers = _scoped_providers(current_user, list(PROVIDERS))
    # CASH is a cross-provider derived figure - shown to every role (see
    # get_agent_aggregate above for the same call), only the per-provider
    # forecasts below are scoped to PROVIDER_OPS's own provider.
    results = [forecast_service.forecast_cash(session, agent_id)]
    for p in visible_providers:
        results.append(forecast_service.forecast_provider(session, agent_id, p))

    return [
        ForecastOut(
            target=r.target,
            target_label=r.target_label,
            status=r.status,
            current_balance=round(r.current_balance, 2),
            burn_rate_per_minute=round(r.burn_rate_per_minute, 2) if r.burn_rate_per_minute is not None else None,
            projected_shortage_at=r.projected_shortage_at,
            minutes_to_shortage=round(r.minutes_to_shortage, 1) if r.minutes_to_shortage is not None else None,
            confidence=r.confidence,
            confidence_note=r.confidence_note,
            top_contributors=r.top_contributors,
        )
        for r in results
    ]


@router.get("/anomaly/{agent_id}", response_model=list[AnomalyOut])
def get_agent_anomalies(
    agent_id: str,
    provider: str = Query(None, description="Limit to one provider (bkash/nagad/rocket); omit to check all three."),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_shared_db),
):
    """Not explicitly named in the brief's endpoint list, but added so the
    rule-based detector required by this phase has a demonstrable, sampleable
    output on its own - Phase 6's alert engine will be what turns a flagged
    result here into a routed, owned Alert/Case."""
    _require_agent_scope(current_user, agent_id)
    requested = [provider] if provider else list(PROVIDERS)
    unknown = set(requested) - set(PROVIDERS)
    if unknown:
        raise HTTPException(400, f"Unknown provider(s): {sorted(unknown)}. Valid: {list(PROVIDERS)}")
    providers = _scoped_providers(current_user, requested)

    results = [anomaly_service.detect_velocity_and_clustering(session, agent_id, p) for p in providers]
    return [
        AnomalyOut(
            agent_id=r.agent_id,
            provider=r.provider,
            flagged=r.flagged,
            window_count=r.window_count,
            baseline_mean=round(r.baseline_mean, 2),
            baseline_stdev=round(r.baseline_stdev, 2),
            z_score=round(r.z_score, 2) if r.z_score is not None else None,
            unique_customers=r.unique_customers,
            concentration_ratio=round(r.concentration_ratio, 2) if r.concentration_ratio is not None else None,
            amount_min=r.amount_min,
            amount_max=r.amount_max,
            amount_coefficient_of_variation=(
                round(r.amount_coefficient_of_variation, 3) if r.amount_coefficient_of_variation is not None else None
            ),
            sample_transaction_ids=r.sample_transaction_ids,
            window_start=r.window_start,
            window_end=r.window_end,
            confidence=r.confidence,
            message=r.message,
        )
        for r in results
    ]


@router.get("/anomaly/{agent_id}/historical", response_model=list[AmountOutlierOut])
def get_agent_historical_outliers(
    agent_id: str,
    provider: str = Query(None, description="Limit to one provider (bkash/nagad/rocket); omit to check all three."),
    transaction_type: str = Query("cash_out", description="cash_out or cash_in"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_shared_db),
):
    """Separate question from /anomaly above: not 'is there a burst right
    now' but 'is this agent's most recent transaction unusual for what THIS
    agent specifically tends to do', judged against their own historical
    distribution. Needs real historical depth to mean anything - see
    provider-api/app/historical_seed.py."""
    _require_agent_scope(current_user, agent_id)
    requested = [provider] if provider else list(PROVIDERS)
    unknown = set(requested) - set(PROVIDERS)
    if unknown:
        raise HTTPException(400, f"Unknown provider(s): {sorted(unknown)}. Valid: {list(PROVIDERS)}")
    if transaction_type not in ("cash_out", "cash_in"):
        raise HTTPException(400, "transaction_type must be 'cash_out' or 'cash_in'")
    providers = _scoped_providers(current_user, requested)

    results = [
        anomaly_service.detect_amount_outlier(session, agent_id, p, transaction_type=transaction_type)
        for p in providers
    ]
    return [
        AmountOutlierOut(
            agent_id=r.agent_id,
            provider=r.provider,
            transaction_type=r.transaction_type,
            flagged=r.flagged,
            evaluated_transaction_id=r.evaluated_transaction_id,
            evaluated_amount=round(r.evaluated_amount, 2) if r.evaluated_amount is not None else None,
            evaluated_at=r.evaluated_at,
            historical_sample_size=r.historical_sample_size,
            historical_mean=round(r.historical_mean, 2) if r.historical_mean is not None else None,
            historical_stdev=round(r.historical_stdev, 2) if r.historical_stdev is not None else None,
            z_score=round(r.z_score, 2) if r.z_score is not None else None,
            confidence=r.confidence,
            message=r.message,
        )
        for r in results
    ]

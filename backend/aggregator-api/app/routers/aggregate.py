from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_shared_db
from app.models import ProviderBalance
from app.schemas import (
    AgentAggregateOut,
    AIRecommendationOut,
    AlertOut,
    AmountOutlierOut,
    AnomalyOut,
    ForecastOut,
    ProviderBalanceOut,
)
from app.services import alerts as alerts_service
from app.services import anomaly as anomaly_service
from app.services import forecast as forecast_service
from app.services.cash import PROVIDERS, evaluate_cash
from app.services.confidence import provider_confidence, weakest

router = APIRouter(prefix="/aggregate", tags=["aggregate"])


@router.get("/agent/{agent_id}", response_model=AgentAggregateOut)
def get_agent_aggregate(agent_id: str, session: Session = Depends(get_shared_db)):
    cash_balance, cash_confidence, cash_note = evaluate_cash(session, agent_id)

    provider_rows = {
        p: session.exec(
            select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == p)
        ).one_or_none()
        for p in PROVIDERS
    }

    if all(row is None for row in provider_rows.values()):
        raise HTTPException(404, f"Agent '{agent_id}' not found - no provider has ever synced data for it")

    providers_out = []
    confidences = [cash_confidence]
    for p in PROVIDERS:
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


@router.get("/forecast/{agent_id}", response_model=list[ForecastOut])
def get_agent_forecast(agent_id: str, session: Session = Depends(get_shared_db)):
    exists = any(
        session.exec(
            select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == p)
        ).one_or_none()
        for p in PROVIDERS
    )
    if not exists:
        raise HTTPException(404, f"Agent '{agent_id}' not found - no provider has ever synced data for it")

    results = [forecast_service.forecast_cash(session, agent_id)]
    for p in PROVIDERS:
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
    session: Session = Depends(get_shared_db),
):
    """Not explicitly named in the brief's endpoint list, but added so the
    rule-based detector required by this phase has a demonstrable, sampleable
    output on its own - Phase 6's alert engine will be what turns a flagged
    result here into a routed, owned Alert/Case."""
    providers = [provider] if provider else list(PROVIDERS)
    unknown = set(providers) - set(PROVIDERS)
    if unknown:
        raise HTTPException(400, f"Unknown provider(s): {sorted(unknown)}. Valid: {list(PROVIDERS)}")

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


@router.get("/alerts/{agent_id}", response_model=list[AlertOut])
def get_agent_alerts(agent_id: str, session: Session = Depends(get_shared_db)):
    """Layers a routed recommendation - rule-based action plus an additive
    AI-generated one (services/llm.py) - on top of forecast_cash/
    forecast_provider/detect_velocity_and_clustering exactly as they already
    run for /forecast and /anomaly above. Nothing about whether something is
    flagged changes here; this only decides what to say once it is."""
    exists = any(
        session.exec(
            select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == p)
        ).one_or_none()
        for p in PROVIDERS
    )
    if not exists:
        raise HTTPException(404, f"Agent '{agent_id}' not found - no provider has ever synced data for it")

    results = alerts_service.build_alerts(session, agent_id)
    return [
        AlertOut(
            category=r.category,
            metric=r.metric,
            severity=r.severity,
            agent_id=r.agent_id,
            provider=r.provider,
            title=r.title,
            message=r.message,
            evidence=r.evidence,
            confidence=r.confidence,
            confidence_note=r.confidence_note,
            recommended_action=r.recommended_action,
            ai_recommendation=AIRecommendationOut(
                text=r.ai_recommendation.text,
                source=r.ai_recommendation.source,
                note=r.ai_recommendation.note,
            ),
        )
        for r in results
    ]


@router.get("/anomaly/{agent_id}/historical", response_model=list[AmountOutlierOut])
def get_agent_historical_outliers(
    agent_id: str,
    provider: str = Query(None, description="Limit to one provider (bkash/nagad/rocket); omit to check all three."),
    transaction_type: str = Query("cash_out", description="cash_out or cash_in"),
    session: Session = Depends(get_shared_db),
):
    """Separate question from /anomaly above: not 'is there a burst right
    now' but 'is this agent's most recent transaction unusual for what THIS
    agent specifically tends to do', judged against their own historical
    distribution. Needs real historical depth to mean anything - see
    provider-api/app/historical_seed.py."""
    providers = [provider] if provider else list(PROVIDERS)
    unknown = set(providers) - set(PROVIDERS)
    if unknown:
        raise HTTPException(400, f"Unknown provider(s): {sorted(unknown)}. Valid: {list(PROVIDERS)}")
    if transaction_type not in ("cash_out", "cash_in"):
        raise HTTPException(400, "transaction_type must be 'cash_out' or 'cash_in'")

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

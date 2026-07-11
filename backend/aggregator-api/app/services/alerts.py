"""Combines the existing rule-based forecast/anomaly detectors with an
additive AI-generated recommendation (services/llm.py) into alert-shaped
results.

Computed on request, never persisted - aggregator-api's Postgres role is
SELECT-only on shared_db (see db.py), so there is nowhere here to durably
store an Alert/Case row the way backend/app does. services/forecast.py and
services/anomaly.py themselves are not modified by this module; this only
adds a routing action + AI recommendation on top of their output.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.config import CASH_SAFETY_THRESHOLD, PROVIDER_SAFETY_THRESHOLD
from app.services import anomaly as anomaly_service
from app.services import forecast as forecast_service
from app.services import llm
from app.services import ml_forecast
from app.services.cash import PROVIDERS
from app.services.confidence import ConfidenceLevel

_LIQUIDITY_ACTION_CASH = "Arrange additional physical cash for this outlet before the projected shortage time."
_LIQUIDITY_ACTION_PROVIDER = "Coordinate an approved provider-specific float support request with {provider} Operations."
_ANOMALY_ACTION = (
    "Review the flagged transactions before approving any large cash replenishment; "
    "escalate to Risk/Compliance if the pattern continues."
)


@dataclass
class AlertResult:
    category: str  # LIQUIDITY | ANOMALY
    metric: str
    severity: str  # LOW | MEDIUM | HIGH
    agent_id: str
    provider: Optional[str]  # None = shared cash
    title: str
    message: str
    evidence: dict
    confidence: ConfidenceLevel
    confidence_note: str
    recommended_action: str  # rule-based, unchanged routing convention
    ai_recommendation: llm.AIRecommendation


def _liquidity_severity(forecast_result) -> str:
    if forecast_result.minutes_to_shortage is None:
        return "MEDIUM"
    if forecast_result.minutes_to_shortage <= 30:
        return "HIGH"
    if forecast_result.minutes_to_shortage <= 90:
        return "MEDIUM"
    return "LOW"


def _liquidity_alert(session: Session, agent_id: str, agent_name: str, forecast_result, now=None) -> AlertResult:
    is_cash = forecast_result.target == "CASH"
    action = (
        _LIQUIDITY_ACTION_CASH if is_cash else _LIQUIDITY_ACTION_PROVIDER.format(provider=forecast_result.target_label)
    )
    eta = (
        f"around {forecast_result.projected_shortage_at.strftime('%H:%M')}"
        if forecast_result.projected_shortage_at
        else "at an unknown time"
    )
    message = f"{forecast_result.target_label} for {agent_name} may run out {eta}."
    fallback_text = f"{action} {message}"

    threshold = CASH_SAFETY_THRESHOLD if is_cash else PROVIDER_SAFETY_THRESHOLD
    ml_prediction = ml_forecast.predict(
        session, agent_id, forecast_result.target, forecast_result.current_balance, threshold, now=now
    )

    ai = llm.recommend_liquidity(agent_name, forecast_result, fallback_text, ml_prediction=ml_prediction)

    return AlertResult(
        category="LIQUIDITY",
        metric="cash_burn_rate" if is_cash else "provider_burn_rate",
        severity=_liquidity_severity(forecast_result),
        agent_id=agent_id,
        provider=None if is_cash else forecast_result.target,
        title=f"{forecast_result.target_label} may run low",
        message=message,
        evidence={
            "current_balance": round(forecast_result.current_balance, 2),
            "burn_rate_per_minute": (
                round(forecast_result.burn_rate_per_minute, 2) if forecast_result.burn_rate_per_minute is not None else None
            ),
            "minutes_to_shortage": (
                round(forecast_result.minutes_to_shortage, 1) if forecast_result.minutes_to_shortage is not None else None
            ),
            "projected_shortage_at": (
                forecast_result.projected_shortage_at.isoformat() if forecast_result.projected_shortage_at else None
            ),
            "top_contributors": forecast_result.top_contributors,
            "ml_prediction": asdict(ml_prediction) if ml_prediction is not None else None,
        },
        confidence=forecast_result.confidence,
        confidence_note=forecast_result.confidence_note,
        recommended_action=action,
        ai_recommendation=ai,
    )


def _anomaly_severity(anomaly_result) -> str:
    if anomaly_result.z_score is not None and anomaly_result.z_score >= 4.0:
        return "HIGH"
    return "MEDIUM"


def _anomaly_alert(agent_id: str, agent_name: str, provider: str, anomaly_result) -> AlertResult:
    fallback_text = f"{_ANOMALY_ACTION} {anomaly_result.message}"
    ai = llm.recommend_anomaly(agent_name, provider, anomaly_result, fallback_text)

    return AlertResult(
        category="ANOMALY",
        metric="velocity_clustering",
        severity=_anomaly_severity(anomaly_result),
        agent_id=agent_id,
        provider=provider,
        title=f"Unusual {provider} cash-out activity - requires review",
        message=anomaly_result.message,
        evidence={
            "window_count": anomaly_result.window_count,
            "baseline_mean": anomaly_result.baseline_mean,
            "baseline_stdev": anomaly_result.baseline_stdev,
            "z_score": anomaly_result.z_score,
            "unique_customers": anomaly_result.unique_customers,
            "concentration_ratio": anomaly_result.concentration_ratio,
            "amount_min": anomaly_result.amount_min,
            "amount_max": anomaly_result.amount_max,
            "sample_transaction_ids": anomaly_result.sample_transaction_ids,
        },
        confidence=anomaly_result.confidence,
        confidence_note=anomaly_result.message,
        recommended_action=_ANOMALY_ACTION,
        ai_recommendation=ai,
    )


def build_alerts(
    session: Session, agent_id: str, agent_name: Optional[str] = None, now: Optional[datetime] = None
) -> list[AlertResult]:
    agent_name = agent_name or agent_id
    results: list[AlertResult] = []

    cash_forecast = forecast_service.forecast_cash(session, agent_id, now=now)
    if cash_forecast.status == "AT_RISK":
        results.append(_liquidity_alert(session, agent_id, agent_name, cash_forecast, now=now))

    for provider in PROVIDERS:
        provider_forecast = forecast_service.forecast_provider(session, agent_id, provider, now=now)
        if provider_forecast.status == "AT_RISK":
            results.append(_liquidity_alert(session, agent_id, agent_name, provider_forecast, now=now))

        anomaly_result = anomaly_service.detect_velocity_and_clustering(session, agent_id, provider, now=now)
        if anomaly_result.flagged:
            results.append(_anomaly_alert(agent_id, agent_name, provider, anomaly_result))

    return results

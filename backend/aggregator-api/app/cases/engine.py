"""Turns forecast/anomaly/data-quality signals into assigned, owned Alert
rows. This is the only module that creates Alert rows, so the assignment
rule and de-duplication/cooldown logic live in exactly one place.

Reuses the existing forecast/anomaly services and shared_db's own
sync_status (computed genuinely by sync-service, not simulated here) rather
than re-implementing detection - this module only decides "does this
evidence cross the threshold for an alert, and who should own it."
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.agents import AGENT_IDS
from app.cases import narratives
from app.cases.models import Alert, AlertType, CaseEvent, CaseStatus, Severity
from app.cases.routing import assign_initial_owner, recommended_action
from app.config import (
    ALERT_REOPEN_COOLDOWN_MINUTES,
    LIQUIDITY_HIGH_SEVERITY_MINUTES,
    LIQUIDITY_MEDIUM_SEVERITY_MINUTES,
)
from app.models import ProviderBalance, SyncStatus
from app.services import anomaly as anomaly_service
from app.services import forecast as forecast_service
from app.services.cash import PROVIDERS
from app.services.confidence import ConfidenceLevel

logger = logging.getLogger("aggregator-api.alert-engine")


def _liquidity_severity(minutes_to_shortage: Optional[float]) -> Severity:
    if minutes_to_shortage is None:
        return Severity.MEDIUM
    if minutes_to_shortage <= LIQUIDITY_HIGH_SEVERITY_MINUTES:
        return Severity.HIGH
    if minutes_to_shortage <= LIQUIDITY_MEDIUM_SEVERITY_MINUTES:
        return Severity.MEDIUM
    return Severity.LOW


def _has_open_duplicate(
    session: Session, agent_id: str, provider: Optional[str], alert_type: AlertType, metric: str, now: datetime
) -> bool:
    cooldown_start = now - timedelta(minutes=ALERT_REOPEN_COOLDOWN_MINUTES)
    stmt = select(Alert).where(
        Alert.agent_id == agent_id,
        Alert.provider == provider,
        Alert.alert_type == alert_type,
        Alert.metric == metric,
        Alert.created_at >= cooldown_start,
    )
    return any(a.current_status != CaseStatus.CLOSED for a in session.exec(stmt))


def _create_alert(
    session: Session,
    *,
    alert_type: AlertType,
    metric: str,
    severity: Severity,
    agent_id: str,
    provider: Optional[str],
    confidence,
    confidence_note: str,
    evidence: dict,
    title: str,
    message_en: str,
    message_bn: str,
    message_banglish: str,
    now: datetime,
) -> Alert:
    owner = assign_initial_owner(alert_type, severity)
    alert = Alert(
        provider=provider,
        agent_id=agent_id,
        alert_type=alert_type,
        metric=metric,
        severity=severity,
        confidence=confidence,
        confidence_note=confidence_note,
        evidence=evidence,
        title=title,
        message_en=message_en,
        message_bn=message_bn,
        message_banglish=message_banglish,
        recommended_action=recommended_action(alert_type, owner, provider),
        current_owner=owner,
        current_status=CaseStatus.ASSIGNED,
        created_at=now,
        updated_at=now,
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)

    session.add(CaseEvent(alert_id=alert.id, event_type="CREATED", actor="system", created_at=now))
    session.add(
        CaseEvent(
            alert_id=alert.id,
            event_type="ASSIGNED",
            actor="system",
            previous_owner=None,
            new_owner=owner,
            created_at=now,
        )
    )
    session.commit()
    return alert


def evaluate_agent(shared_session: Session, agg_session: Session, agent_id: str, now: Optional[datetime] = None) -> list[Alert]:
    now = now or datetime.utcnow()
    created: list[Alert] = []

    # --- liquidity: shared cash ---------------------------------------
    cash_forecast = forecast_service.forecast_cash(shared_session, agent_id, now=now)
    if cash_forecast.status == "AT_RISK" and not _has_open_duplicate(
        agg_session, agent_id, None, AlertType.LIQUIDITY, "cash_burn_rate", now
    ):
        title, en, bn, banglish = narratives.liquidity_narrative(agent_id, cash_forecast)
        created.append(
            _create_alert(
                agg_session,
                alert_type=AlertType.LIQUIDITY,
                metric="cash_burn_rate",
                severity=_liquidity_severity(cash_forecast.minutes_to_shortage),
                agent_id=agent_id,
                provider=None,
                confidence=cash_forecast.confidence,
                confidence_note=cash_forecast.confidence_note,
                evidence={
                    "current_balance": cash_forecast.current_balance,
                    "burn_rate_per_minute": cash_forecast.burn_rate_per_minute,
                    "minutes_to_shortage": cash_forecast.minutes_to_shortage,
                    "projected_shortage_at": cash_forecast.projected_shortage_at.isoformat()
                    if cash_forecast.projected_shortage_at
                    else None,
                    "top_contributors": cash_forecast.top_contributors,
                },
                title=title,
                message_en=en,
                message_bn=bn,
                message_banglish=banglish,
                now=now,
            )
        )

    # --- liquidity: per-provider e-money --------------------------------
    for provider in PROVIDERS:
        pf = forecast_service.forecast_provider(shared_session, agent_id, provider, now=now)
        if pf.status != "AT_RISK" or _has_open_duplicate(
            agg_session, agent_id, provider, AlertType.LIQUIDITY, "provider_burn_rate", now
        ):
            continue
        title, en, bn, banglish = narratives.liquidity_narrative(agent_id, pf)
        created.append(
            _create_alert(
                agg_session,
                alert_type=AlertType.LIQUIDITY,
                metric="provider_burn_rate",
                severity=_liquidity_severity(pf.minutes_to_shortage),
                agent_id=agent_id,
                provider=provider,
                confidence=pf.confidence,
                confidence_note=pf.confidence_note,
                evidence={
                    "current_balance": pf.current_balance,
                    "burn_rate_per_minute": pf.burn_rate_per_minute,
                    "minutes_to_shortage": pf.minutes_to_shortage,
                    "projected_shortage_at": pf.projected_shortage_at.isoformat() if pf.projected_shortage_at else None,
                },
                title=title,
                message_en=en,
                message_bn=bn,
                message_banglish=banglish,
                now=now,
            )
        )

    # --- anomaly: velocity + account clustering -------------------------
    for provider in PROVIDERS:
        result = anomaly_service.detect_velocity_and_clustering(shared_session, agent_id, provider, now=now)
        if not result.flagged or _has_open_duplicate(
            agg_session, agent_id, provider, AlertType.ANOMALY, "velocity_spike", now
        ):
            continue
        severity = Severity.HIGH if result.z_score is not None and result.z_score >= 4.0 else Severity.MEDIUM
        title, en, bn, banglish = narratives.anomaly_velocity_narrative(agent_id, provider, result)
        created.append(
            _create_alert(
                agg_session,
                alert_type=AlertType.ANOMALY,
                metric="velocity_spike",
                severity=severity,
                agent_id=agent_id,
                provider=provider,
                confidence=result.confidence,
                confidence_note=result.message,
                evidence={
                    "window_count": result.window_count,
                    "baseline_mean": result.baseline_mean,
                    "baseline_stdev": result.baseline_stdev,
                    "z_score": result.z_score,
                    "unique_customers": result.unique_customers,
                    "concentration_ratio": result.concentration_ratio,
                    "amount_min": result.amount_min,
                    "amount_max": result.amount_max,
                    "sample_transaction_ids": result.sample_transaction_ids,
                },
                title=title,
                message_en=en,
                message_bn=bn,
                message_banglish=banglish,
                now=now,
            )
        )

    # --- anomaly: per-agent historical amount outlier -------------------
    for provider in PROVIDERS:
        result = anomaly_service.detect_amount_outlier(shared_session, agent_id, provider, now=now)
        if not result.flagged or _has_open_duplicate(
            agg_session, agent_id, provider, AlertType.ANOMALY, "amount_outlier", now
        ):
            continue
        severity = Severity.HIGH if result.z_score is not None and result.z_score >= 4.5 else Severity.MEDIUM
        title, en, bn, banglish = narratives.amount_outlier_narrative(agent_id, provider, result)
        created.append(
            _create_alert(
                agg_session,
                alert_type=AlertType.ANOMALY,
                metric="amount_outlier",
                severity=severity,
                agent_id=agent_id,
                provider=provider,
                confidence=result.confidence,
                confidence_note=result.message,
                evidence={
                    "evaluated_transaction_id": result.evaluated_transaction_id,
                    "evaluated_amount": result.evaluated_amount,
                    "historical_sample_size": result.historical_sample_size,
                    "historical_mean": result.historical_mean,
                    "historical_stdev": result.historical_stdev,
                    "z_score": result.z_score,
                },
                title=title,
                message_en=en,
                message_bn=bn,
                message_banglish=banglish,
                now=now,
            )
        )

    # --- data quality: feed sync status ---------------------------------
    for provider in PROVIDERS:
        balance = shared_session.exec(
            select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == provider)
        ).one_or_none()
        if balance is None or balance.sync_status == SyncStatus.OK or _has_open_duplicate(
            agg_session, agent_id, provider, AlertType.DATA_QUALITY, "feed_sync_status", now
        ):
            continue
        title, en, bn, banglish = narratives.data_quality_narrative(
            agent_id, provider, balance.sync_status.value, balance.staleness_seconds
        )
        created.append(
            _create_alert(
                agg_session,
                alert_type=AlertType.DATA_QUALITY,
                metric="feed_sync_status",
                severity=Severity.MEDIUM,
                agent_id=agent_id,
                provider=provider,
                confidence=ConfidenceLevel.LOW,
                confidence_note=f"{provider} feed is {balance.sync_status.value} - treat any related estimate as low-confidence.",
                evidence={
                    "sync_status": balance.sync_status.value,
                    "staleness_seconds": balance.staleness_seconds,
                    "source_updated_at": balance.source_updated_at.isoformat(),
                },
                title=title,
                message_en=en,
                message_bn=bn,
                message_banglish=banglish,
                now=now,
            )
        )

    return created


def evaluate_all(shared_session: Session, agg_session: Session, now: Optional[datetime] = None) -> int:
    total = 0
    for agent_id in AGENT_IDS:
        try:
            total += len(evaluate_agent(shared_session, agg_session, agent_id, now=now))
        except Exception:
            logger.exception("evaluate_agent(%s) raised - skipping this agent this cycle", agent_id)
    return total

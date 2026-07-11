"""Turns analytics output into Alert + Case rows.

This is the only module that writes Alert/Case/CaseEvent rows, so the
routing table and de-duplication rule live in exactly one place.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.alerts.routing import get_routing
from app.analytics.anomaly import detect_velocity_spike
from app.analytics.forecaster import ForecastResult, forecast_cash, forecast_provider
from app.core.config import ALERT_REOPEN_COOLDOWN_MINUTES, FEED_STALE_AFTER_SECONDS
from app.models.models import (
    Agent,
    Alert,
    AlertEvent,
    AlertCategory,
    Case,
    CaseEvent,
    CaseStatus,
    ConfidenceLevel,
    DataFeedStatus,
    DataQuality,
    FeedHealth,
    Provider,
)
from app.services import llm


def evaluate_agent(session: Session, agent_id: str, now: Optional[datetime] = None) -> list[Alert]:
    now = now or datetime.utcnow()
    agent = session.get(Agent, agent_id)
    providers = list(session.exec(select(Provider)))
    provider_names = {p.id: p.name for p in providers}

    created: list[Alert] = []

    # --- data feed health -> safe fallback -------------------------------
    stale_providers: set[str] = set()
    for provider in providers:
        feed = session.exec(
            select(DataFeedStatus).where(
                DataFeedStatus.agent_id == agent_id, DataFeedStatus.provider_id == provider.id
            )
        ).one()
        is_stale = feed.frozen or (now - feed.last_update_at).total_seconds() > FEED_STALE_AFTER_SECONDS
        new_health = FeedHealth.STALE if is_stale else FeedHealth.OK
        if new_health != feed.health:
            feed.health = new_health
            session.add(feed)
            session.commit()
        if is_stale:
            stale_providers.add(provider.id)
            alert = _maybe_create_alert(
                session,
                category=AlertCategory.DATA_QUALITY,
                metric="feed_staleness",
                severity="MEDIUM",
                agent_id=agent_id,
                provider_id=provider.id,
                now=now,
                build=lambda p=provider: _build_data_quality(agent.name, p, feed),
            )
            if alert:
                created.append(alert)

    # --- liquidity: shared cash -------------------------------------------
    # Confidence gate decided *before* any staleness downgrade below: a
    # genuinely low-confidence trend (sparse/noisy own-ledger data) is
    # suppressed as noise, while a confident trend that only becomes LOW
    # confidence because a feed is stale still fires - shown with reduced
    # confidence and a caveat, per Scenario C, rather than silently dropped.
    cash_forecast = forecast_cash(session, agent_id, now=now)
    should_alert_cash = cash_forecast.status == "AT_RISK"
    if stale_providers:
        cash_forecast.data_quality = DataQuality.DEGRADED
        cash_forecast.confidence = ConfidenceLevel.LOW
        cash_forecast.confidence_note += (
            f" Note: {', '.join(provider_names[p] for p in stale_providers)} feed is delayed; "
            "this estimate may be unreliable."
        )
    if should_alert_cash:
        alert = _maybe_create_alert(
            session,
            category=AlertCategory.LIQUIDITY,
            metric="cash_burn_rate",
            severity=_liquidity_severity(cash_forecast),
            agent_id=agent_id,
            provider_id=None,
            now=now,
            build=lambda: _build_liquidity(agent.name, cash_forecast, provider_names),
        )
        if alert:
            created.append(alert)

    # --- liquidity: per-provider e-money ----------------------------------
    for provider in providers:
        provider_forecast = forecast_provider(session, agent_id, provider.id, now=now)
        if provider_forecast.status != "AT_RISK":
            continue
        if provider.id in stale_providers:
            provider_forecast.data_quality = DataQuality.DEGRADED
            provider_forecast.confidence = ConfidenceLevel.LOW
            provider_forecast.confidence_note += " Note: this provider's feed is delayed; estimate may be unreliable."
        alert = _maybe_create_alert(
            session,
            category=AlertCategory.LIQUIDITY,
            metric="provider_burn_rate",
            severity=_liquidity_severity(provider_forecast),
            agent_id=agent_id,
            provider_id=provider.id,
            now=now,
            build=lambda pf=provider_forecast: _build_liquidity(agent.name, pf, provider_names),
        )
        if alert:
            created.append(alert)

    # --- anomaly: velocity spike per provider ------------------------------
    for provider in providers:
        anomaly = detect_velocity_spike(session, agent_id, provider.id, now=now)
        if not anomaly.flagged:
            continue
        severity = "HIGH" if anomaly.z_score is not None and anomaly.z_score >= 4.0 else "MEDIUM"
        alert = _maybe_create_alert(
            session,
            category=AlertCategory.ANOMALY,
            metric="velocity_spike",
            severity=severity,
            agent_id=agent_id,
            provider_id=provider.id,
            now=now,
            build=lambda a=anomaly, p=provider: _build_anomaly(agent.name, p, a),
        )
        if alert:
            created.append(alert)

    return created


def _liquidity_severity(forecast: ForecastResult) -> str:
    if forecast.minutes_to_shortage is None:
        return "MEDIUM"
    if forecast.minutes_to_shortage <= 30:
        return "HIGH"
    if forecast.minutes_to_shortage <= 90:
        return "MEDIUM"
    return "LOW"


def _build_liquidity(agent_name: str, forecast: ForecastResult, provider_names: dict[str, str]):
    narrative = llm.liquidity(agent_name, forecast, provider_names)
    evidence = {
        "current_balance": forecast.current_balance,
        "burn_rate_per_minute": forecast.burn_rate_per_minute,
        "minutes_to_shortage": forecast.minutes_to_shortage,
        "projected_shortage_at": forecast.projected_shortage_at.isoformat() if forecast.projected_shortage_at else None,
        "top_contributors": forecast.top_contributors,
    }
    return (narrative.title, narrative.english, narrative.bangla, narrative.banglish, evidence, forecast.confidence,
            forecast.confidence_note, forecast.data_quality)


def _build_anomaly(agent_name: str, provider: Provider, anomaly):
    narrative = llm.anomaly(agent_name, provider.id, provider.name, anomaly)
    evidence = {
        "window_count": anomaly.window_count,
        "baseline_mean": anomaly.baseline_mean,
        "baseline_stdev": anomaly.baseline_stdev,
        "z_score": anomaly.z_score,
        "unique_customers": anomaly.unique_customers,
        "amount_min": anomaly.amount_min,
        "amount_max": anomaly.amount_max,
        "sample_transaction_ids": anomaly.sample_transaction_ids,
    }
    return (narrative.title, narrative.english, narrative.bangla, narrative.banglish, evidence, anomaly.confidence,
            anomaly.confidence_note, DataQuality.OK)


def _build_data_quality(agent_name: str, provider: Provider, feed: DataFeedStatus):
    narrative = llm.data_quality(agent_name, provider.id, provider.name)
    evidence = {
        "last_update_at": feed.last_update_at.isoformat(),
        "seconds_since_update": (datetime.utcnow() - feed.last_update_at).total_seconds(),
        "note": feed.note,
    }
    return (narrative.title, narrative.english, narrative.bangla, narrative.banglish, evidence, ConfidenceLevel.LOW,
            "Feed has not reported recently.", DataQuality.DEGRADED)


def _maybe_create_alert(
    session: Session,
    *,
    category: AlertCategory,
    metric: str,
    severity: str,
    agent_id: str,
    provider_id: Optional[str],
    now: datetime,
    build,
) -> Optional[Alert]:
    if _has_recent_open_alert(session, agent_id, provider_id, category, metric, now):
        return None

    title, message_en, message_bn, message_banglish, evidence, confidence, confidence_note, data_quality = build()

    alert = Alert(
        category=category,
        metric=metric,
        severity=severity,
        agent_id=agent_id,
        provider_id=provider_id,
        title=title,
        message_en=message_en,
        message_bn=message_bn,
        message_banglish=message_banglish,
        evidence=evidence,
        confidence=confidence,
        confidence_note=confidence_note,
        data_quality=data_quality,
        created_at=now,
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)

    provider = session.get(Provider, provider_id) if provider_id else None
    routing = get_routing(category, provider_id, provider.name if provider else None)

    case = Case(
        alert_id=alert.id,
        stakeholder_role=routing["role"],
        owner=routing["owner"],
        status=CaseStatus.NEW,
        recommended_action=routing["action"],
        created_at=now,
        updated_at=now,
    )
    session.add(case)
    session.commit()
    session.refresh(case)

    session.add(
        CaseEvent(
            case_id=case.id,
            event_type="CREATED",
            note=f"Alert auto-generated by the analytics engine and routed to {routing['role']}.",
            actor="system",
            created_at=now,
        )
    )
    session.add(
        AlertEvent(
            alert_id=alert.id,
            event_type="CREATED",
            actor="system",
            note="Alert generated automatically after synchronization.",
            owner_role=routing["owner_role"],
            created_at=now,
        )
    )
    session.commit()

    return alert


def _has_recent_open_alert(
    session: Session,
    agent_id: str,
    provider_id: Optional[str],
    category: AlertCategory,
    metric: str,
    now: datetime,
) -> bool:
    cooldown_start = now - timedelta(minutes=ALERT_REOPEN_COOLDOWN_MINUTES)
    stmt = select(Alert).where(
        Alert.agent_id == agent_id,
        Alert.provider_id == provider_id,
        Alert.category == category,
        Alert.metric == metric,
        Alert.created_at >= cooldown_start,
    )
    recent_alerts = list(session.exec(stmt))
    if not recent_alerts:
        return False
    for alert in recent_alerts:
        case = session.exec(select(Case).where(Case.alert_id == alert.id)).one_or_none()
        if case is None or case.status != CaseStatus.RESOLVED:
            return True
    return False

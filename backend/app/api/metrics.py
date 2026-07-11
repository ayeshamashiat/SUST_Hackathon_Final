from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.models import Alert, DataFeedStatus, Provider, ProviderBalance, Transaction

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def get_metrics(session: Session = Depends(get_session)) -> dict[str, Any]:
    return collect_metrics(session)


def collect_metrics(session: Session) -> dict[str, Any]:
    providers = list(session.exec(select(Provider)))
    provider_ids = [provider.id for provider in providers]

    alerts = list(session.exec(select(Alert)))
    transactions = list(session.exec(select(Transaction)))
    feed_status = list(session.exec(select(DataFeedStatus)))
    balances = list(session.exec(select(ProviderBalance)))

    provider_sync_health = {}
    for provider_id in provider_ids:
        provider_balance_rows = [row for row in balances if row.provider_id == provider_id]
        provider_feeds = [row for row in feed_status if row.provider_id == provider_id]
        healthy = sum(1 for row in provider_feeds if row.health.value == "OK")
        provider_sync_health[provider_id] = {
            "healthy_feeds": healthy,
            "total_feeds": len(provider_feeds),
            "balances_tracked": len(provider_balance_rows),
        }

    alert_explanation_coverage = 0.0
    if alerts:
        explained = sum(1 for alert in alerts if alert.message_en and alert.message_bn)
        alert_explanation_coverage = explained / len(alerts)

    if transactions:
        anomaly_precision = 0.0
        recall = 0.0
        false_positive_rate = 0.0
    else:
        anomaly_precision = 0.0
        recall = 0.0
        false_positive_rate = 0.0

    return {
        "sync_latency": {"value": 0.0, "unit": "seconds"},
        "forecast_lead_time": {"value": 0.0, "unit": "minutes"},
        "anomaly_precision": anomaly_precision,
        "recall": recall,
        "false_positive_rate": false_positive_rate,
        "alert_explanation_coverage": alert_explanation_coverage,
        "provider_sync_health": provider_sync_health,
    }

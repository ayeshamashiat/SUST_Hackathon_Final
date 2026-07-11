from datetime import datetime, timedelta

from app.api.agents import get_transactions
from app.api.metrics import collect_metrics
from app.models.models import Transaction, TransactionStatus, TransactionType


def _seed_transactions(session, provider_id: str, amount: float, created_at: datetime) -> None:
    session.add(
        Transaction(
            agent_id="testagent",
            provider_id=provider_id,
            type=TransactionType.CASH_OUT,
            amount=amount,
            customer_ref=f"{provider_id}-txn",
            area="TestArea",
            status=TransactionStatus.SUCCESS,
            created_at=created_at,
        )
    )
    session.commit()


def test_provider_queries_do_not_cross_provider_boundaries(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    _seed_transactions(agent_setup, "bkash", 100.0, now - timedelta(minutes=10))
    _seed_transactions(agent_setup, "nagad", 200.0, now - timedelta(minutes=8))
    _seed_transactions(agent_setup, "rocket", 300.0, now - timedelta(minutes=6))

    for provider_id in ("bkash", "nagad", "rocket"):
        rows = get_transactions("testagent", provider_id=provider_id, session=agent_setup)
        assert rows, f"expected transactions for {provider_id}"
        assert all(row.provider_id == provider_id for row in rows)
        assert all(row.agent_id == "testagent" for row in rows)


def test_collect_metrics_returns_expected_shape(agent_setup):
    metrics = collect_metrics(agent_setup)

    assert set(metrics) >= {
        "sync_latency",
        "forecast_lead_time",
        "anomaly_precision",
        "recall",
        "false_positive_rate",
        "alert_explanation_coverage",
        "provider_sync_health",
    }
    assert isinstance(metrics["provider_sync_health"], dict)
    assert set(metrics["provider_sync_health"]) >= {"bkash", "nagad", "rocket"}
    assert metrics["anomaly_precision"] >= 0.0
    assert metrics["recall"] >= 0.0
    assert metrics["false_positive_rate"] >= 0.0

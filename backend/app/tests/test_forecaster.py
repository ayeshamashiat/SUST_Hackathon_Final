from datetime import datetime, timedelta

from app.analytics.forecaster import forecast_cash
from app.core.config import CASH_SAFETY_THRESHOLD
from app.models.models import Transaction, TransactionStatus, TransactionType


def _add_tx(session, *, provider_id, tx_type, amount, created_at, status=TransactionStatus.SUCCESS):
    session.add(
        Transaction(
            agent_id="testagent",
            provider_id=provider_id,
            type=tx_type,
            amount=amount,
            customer_ref="CUST-0001",
            area="TestArea",
            status=status,
            created_at=created_at,
        )
    )
    session.commit()


def test_insufficient_data_with_few_transactions(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(2):
        _add_tx(agent_setup, provider_id="bkash", tx_type=TransactionType.CASH_OUT, amount=1000, created_at=now - timedelta(minutes=i))
    result = forecast_cash(agent_setup, "testagent", now=now)
    assert result.status == "INSUFFICIENT_DATA"
    assert result.confidence.value == "LOW"


def test_short_noisy_window_is_not_treated_as_at_risk(agent_setup):
    """Regression test: a handful of draining transactions within a few
    seconds must not be extrapolated into a confident shortage ETA - this
    was the bug that made a healthy, low-traffic agent look at-risk."""
    now = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(6):
        _add_tx(
            agent_setup,
            provider_id="bkash",
            tx_type=TransactionType.CASH_OUT,
            amount=1000,
            created_at=now - timedelta(seconds=5 * i),
        )
    result = forecast_cash(agent_setup, "testagent", now=now)
    assert result.status == "INSUFFICIENT_DATA"


def test_consistent_drain_is_flagged_at_risk(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(8):
        _add_tx(
            agent_setup,
            provider_id="bkash",
            tx_type=TransactionType.CASH_OUT,
            amount=1000,
            created_at=now - timedelta(minutes=i),
        )
    result = forecast_cash(agent_setup, "testagent", now=now)
    assert result.status == "AT_RISK"
    assert result.projected_shortage_at is not None
    assert result.confidence.value in ("MEDIUM", "HIGH")
    # 20,000 balance, 5,000 threshold, draining ~1,000/min -> ~15 min out
    assert 10 <= result.minutes_to_shortage <= 20


def test_growing_balance_is_stable(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(8):
        _add_tx(
            agent_setup,
            provider_id="bkash",
            tx_type=TransactionType.CASH_IN,
            amount=1000,
            created_at=now - timedelta(minutes=i),
        )
    result = forecast_cash(agent_setup, "testagent", now=now)
    assert result.status == "STABLE"
    assert result.projected_shortage_at is None


def test_mixed_direction_noise_is_not_significant(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    amounts_and_types = [
        (500, TransactionType.CASH_OUT),
        (480, TransactionType.CASH_IN),
        (510, TransactionType.CASH_OUT),
        (495, TransactionType.CASH_IN),
        (505, TransactionType.CASH_OUT),
        (500, TransactionType.CASH_IN),
    ]
    for i, (amount, tx_type) in enumerate(amounts_and_types):
        _add_tx(agent_setup, provider_id="bkash", tx_type=tx_type, amount=amount, created_at=now - timedelta(minutes=i))
    result = forecast_cash(agent_setup, "testagent", now=now)
    assert result.status == "STABLE"


def test_failed_transactions_are_excluded_from_the_trend(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(8):
        _add_tx(
            agent_setup,
            provider_id="bkash",
            tx_type=TransactionType.CASH_OUT,
            amount=1000,
            created_at=now - timedelta(minutes=i),
            status=TransactionStatus.FAILED,
        )
    result = forecast_cash(agent_setup, "testagent", now=now)
    assert result.status == "INSUFFICIENT_DATA"


def test_safety_threshold_is_the_projection_floor(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(8):
        _add_tx(
            agent_setup,
            provider_id="bkash",
            tx_type=TransactionType.CASH_OUT,
            amount=1000,
            created_at=now - timedelta(minutes=i),
        )
    result = forecast_cash(agent_setup, "testagent", now=now)
    expected_minutes = (20_000 - CASH_SAFETY_THRESHOLD) / abs(result.burn_rate_per_minute)
    assert abs(result.minutes_to_shortage - expected_minutes) < 0.01

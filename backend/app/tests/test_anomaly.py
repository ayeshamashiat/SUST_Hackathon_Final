from datetime import datetime, timedelta

from app.analytics.anomaly import detect_velocity_spike
from app.models.models import Transaction, TransactionStatus, TransactionType


def _add_cashouts(session, provider_id, now, minute_offsets, customer_prefix="CUST"):
    for i, offset in enumerate(minute_offsets):
        session.add(
            Transaction(
                agent_id="testagent",
                provider_id=provider_id,
                type=TransactionType.CASH_OUT,
                amount=1000,
                customer_ref=f"{customer_prefix}-{i:04d}",
                area="TestArea",
                status=TransactionStatus.SUCCESS,
                created_at=now - timedelta(minutes=offset),
            )
        )
    session.commit()


# Baseline: four 6-minute buckets covering [-30, -6) minutes with counts
# 5, 6, 7, 6 (mean 6, stdev ~0.71) - a mildly varying but stable baseline.
_BASELINE_OFFSETS = [29, 28, 27, 26, 25, 23, 22, 21, 20, 19, 18.5, 17, 16, 15, 14, 13, 12.5, 12.2, 11, 10, 9, 8, 7, 6.5]


def test_no_baseline_is_not_flagged(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    _add_cashouts(agent_setup, "bkash", now, [5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2])
    result = detect_velocity_spike(agent_setup, "testagent", "bkash", now=now)
    assert result.flagged is False
    assert result.confidence.value == "LOW"


def test_steady_traffic_is_not_flagged(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    _add_cashouts(agent_setup, "bkash", now, _BASELINE_OFFSETS, customer_prefix="BASE")
    _add_cashouts(agent_setup, "bkash", now, [5.5, 4.5, 3.5, 2.5, 1.5, 0.5], customer_prefix="WIN")
    result = detect_velocity_spike(agent_setup, "testagent", "bkash", now=now)
    assert result.flagged is False


def test_genuine_spike_is_flagged_with_evidence(agent_setup):
    now = datetime(2026, 1, 1, 12, 0, 0)
    _add_cashouts(agent_setup, "bkash", now, _BASELINE_OFFSETS, customer_prefix="BASE")
    window_offsets = [5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.9, 0.8, 0.7, 0.6, 0.5]
    _add_cashouts(agent_setup, "bkash", now, window_offsets, customer_prefix="WIN")
    result = detect_velocity_spike(agent_setup, "testagent", "bkash", now=now)
    assert result.flagged is True
    assert result.z_score is not None and result.z_score >= 2.0
    assert result.window_count == len(window_offsets)
    assert len(result.sample_transaction_ids) > 0


def test_different_provider_is_unaffected(agent_setup):
    """Evidence for one provider should never leak into another provider's
    detection - provider boundaries must hold inside the analytics layer too."""
    now = datetime(2026, 1, 1, 12, 0, 0)
    _add_cashouts(agent_setup, "bkash", now, _BASELINE_OFFSETS, customer_prefix="BASE")
    window_offsets = [5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.9, 0.8, 0.7, 0.6, 0.5]
    _add_cashouts(agent_setup, "bkash", now, window_offsets, customer_prefix="WIN")

    result = detect_velocity_spike(agent_setup, "testagent", "nagad", now=now)
    assert result.flagged is False
    assert result.window_count == 0

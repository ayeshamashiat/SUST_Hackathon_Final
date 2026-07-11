"""One sync cycle, per provider: poll -> idempotently project new
transactions -> reconcile + upsert the current balance projection ->
compute staleness_seconds and sync_status.

sync_status priority for a given (agent, provider) row: FAILED (the poll
itself raised) > CONFLICTING (the provider's own balance doesn't reconcile
with its own transaction history, from what we've now seen) > DELAYED
(source hasn't updated recently enough) > OK. Only one status is stored per
row, so this order is a deliberate severity ranking, not an accident of
which check happens to run last.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import select

from app.config import settings
from app.db import PROVIDER_ENGINES, provider_session, shared_session
from app.models import ProviderBalance, SyncState, SyncStatus, TransactionProjection
from app.provider_models import Balance as ProviderBalanceRow
from app.provider_models import Transaction as ProviderTransactionRow
from app.provider_models import TransactionType

RECONCILE_EPSILON = 0.01  # float rounding tolerance, not a business threshold


def _get_or_create_sync_state(shared, provider: str) -> SyncState:
    st = shared.get(SyncState, provider)
    if st is None:
        st = SyncState(provider=provider)
        shared.add(st)
        shared.commit()
        shared.refresh(st)
    return st


def _project_new_transactions(
    shared, provider: str, txs: list[ProviderTransactionRow], now: datetime
) -> dict[str, float]:
    """Idempotent: skips any transaction id already projected for this
    provider (defends against re-processing the same batch after a crash
    between insert and watermark-commit, not just relying on the watermark
    alone). Returns the per-agent signed e-money delta for the
    newly-projected rows, used for balance reconciliation."""
    if not txs:
        return {}

    candidate_ids = [t.txn_id for t in txs]
    already_projected = set(
        shared.exec(
            select(TransactionProjection.provider_txn_id).where(
                TransactionProjection.provider == provider,
                TransactionProjection.provider_txn_id.in_(candidate_ids),
            )
        )
    )

    deltas: dict[str, float] = {}
    for tx in txs:
        if tx.txn_id in already_projected:
            continue
        shared.add(
            TransactionProjection(
                provider_txn_id=tx.txn_id,
                agent_id=tx.agent_id,
                provider=provider,
                type=tx.type.value,
                amount=tx.amount,
                account_ref=tx.account_ref,
                occurred_at=tx.timestamp,
                synced_at=now,
                is_injected_anomaly=tx.is_injected_anomaly,
            )
        )
        delta = tx.amount if tx.type == TransactionType.CASH_OUT else -tx.amount
        deltas[tx.agent_id] = deltas.get(tx.agent_id, 0.0) + delta
    return deltas


def _mark_provider_failed(shared, provider: str, now: datetime) -> None:
    """A failed poll means we have no fresh source data at all - keep the
    last known projection (don't fabricate a new balance) but flag every row
    for this provider as FAILED and let staleness keep growing against the
    last confirmed source_updated_at."""
    rows = list(shared.exec(select(ProviderBalance).where(ProviderBalance.provider == provider)))
    for row in rows:
        row.sync_status = SyncStatus.FAILED
        row.synced_at = now
        row.staleness_seconds = (now - row.source_updated_at).total_seconds()
        shared.add(row)
    shared.commit()


def sync_provider(provider: str, now: Optional[datetime] = None) -> None:
    now = now or datetime.utcnow()

    with shared_session() as shared:
        state = _get_or_create_sync_state(shared, provider)
        state.last_poll_attempt_at = now
        shared.add(state)
        shared.commit()

        try:
            with provider_session(provider) as psession:
                balances = list(psession.exec(select(ProviderBalanceRow)))
                new_txs = list(
                    psession.exec(
                        select(ProviderTransactionRow)
                        .where(ProviderTransactionRow.txn_id > state.last_synced_txn_id)
                        .order_by(ProviderTransactionRow.txn_id)
                    )
                )
        except Exception:
            state.consecutive_failures += 1
            shared.add(state)
            shared.commit()
            _mark_provider_failed(shared, provider, now)
            return

        state.consecutive_failures = 0
        state.last_poll_success_at = now

        deltas_by_agent = _project_new_transactions(shared, provider, new_txs, now)
        if new_txs:
            state.last_synced_txn_id = max(t.txn_id for t in new_txs)
        shared.add(state)

        for balance in balances:
            staleness = (now - balance.last_updated).total_seconds()
            existing = shared.exec(
                select(ProviderBalance).where(
                    ProviderBalance.agent_id == balance.agent_id, ProviderBalance.provider == provider
                )
            ).one_or_none()

            status = SyncStatus.OK
            if existing is not None:
                expected = existing.emoney_balance + deltas_by_agent.get(balance.agent_id, 0.0)
                if abs(expected - balance.emoney_balance) > RECONCILE_EPSILON:
                    status = SyncStatus.CONFLICTING
            if status != SyncStatus.CONFLICTING and staleness > settings.sync_stale_after_seconds:
                status = SyncStatus.DELAYED

            if existing is None:
                shared.add(
                    ProviderBalance(
                        agent_id=balance.agent_id,
                        provider=provider,
                        emoney_balance=balance.emoney_balance,
                        source_updated_at=balance.last_updated,
                        synced_at=now,
                        staleness_seconds=staleness,
                        sync_status=status,
                    )
                )
            else:
                existing.emoney_balance = balance.emoney_balance
                existing.source_updated_at = balance.last_updated
                existing.synced_at = now
                existing.staleness_seconds = staleness
                existing.sync_status = status
                shared.add(existing)

        shared.commit()


def sync_all(now: Optional[datetime] = None) -> None:
    for provider in PROVIDER_ENGINES:
        sync_provider(provider, now=now)


def get_status() -> dict:
    with shared_session() as shared:
        states = list(shared.exec(select(SyncState)))
        balances = list(shared.exec(select(ProviderBalance)))

    status_counts: dict[str, dict[str, int]] = {}
    for b in balances:
        status_counts.setdefault(b.provider, {s.value: 0 for s in SyncStatus})
        status_counts[b.provider][b.sync_status.value] += 1

    return {
        "sync_state": [
            {
                "provider": s.provider,
                "last_synced_txn_id": s.last_synced_txn_id,
                "last_poll_attempt_at": s.last_poll_attempt_at,
                "last_poll_success_at": s.last_poll_success_at,
                "consecutive_failures": s.consecutive_failures,
            }
            for s in states
        ],
        "provider_balance_status_counts": status_counts,
        "provider_balances_projected": len(balances),
    }

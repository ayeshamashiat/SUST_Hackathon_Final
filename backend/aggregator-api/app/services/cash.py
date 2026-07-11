"""Derives the shared physical-cash balance for an agent - see config.py's
CASH_OPENING_BALANCE comment for why this is computed here instead of read
from a stored column: nothing in the system currently writes one.
"""

from sqlmodel import Session, select

from app.config import CASH_OPENING_BALANCE
from app.models import ProviderBalance, TransactionProjection
from app.services.confidence import ConfidenceLevel, provider_confidence, weakest

PROVIDERS = ("bkash", "nagad", "rocket")


def compute_cash_balance(session: Session, agent_id: str) -> tuple[float, dict[str, bool]]:
    """Returns the derived cash balance and, per provider, whether any
    transaction history at all was found (False = that provider has never
    been synced for this agent - the derived cash figure is systematically
    understated in that case)."""
    rows = list(session.exec(select(TransactionProjection).where(TransactionProjection.agent_id == agent_id)))

    delta = 0.0
    seen_provider: dict[str, bool] = {p: False for p in PROVIDERS}
    for tx in rows:
        seen_provider[tx.provider] = True
        # CASH_OUT: agent hands physical cash to the customer -> cash drops.
        # CASH_IN: agent receives physical cash -> cash rises. Mirrors the
        # inverse convention already established for e-money in provider-api.
        delta += -tx.amount if tx.type == "cash_out" else tx.amount

    return CASH_OPENING_BALANCE + delta, seen_provider


def evaluate_cash(session: Session, agent_id: str) -> tuple[float, ConfidenceLevel, str]:
    """Cash aggregates all three providers, so its confidence can never be
    better than the least trustworthy provider feeding it - and a provider
    that's never been seen at all is worse than "missing," since the cash
    figure quietly excludes its effect rather than flagging a gap."""
    balance, seen_provider = compute_cash_balance(session, agent_id)

    provider_balances = {
        p: session.exec(
            select(ProviderBalance).where(ProviderBalance.agent_id == agent_id, ProviderBalance.provider == p)
        ).one_or_none()
        for p in PROVIDERS
    }

    confidences = []
    notes = []
    for p in PROVIDERS:
        if not seen_provider[p]:
            confidences.append(ConfidenceLevel.LOW)
            notes.append(f"{p}: no transaction history seen yet - cash figure may be understated.")
            continue
        level, note = provider_confidence(provider_balances[p])
        confidences.append(level)
        if level != ConfidenceLevel.HIGH:
            notes.append(f"{p}: {note}")

    return balance, weakest(*confidences), " ".join(notes)

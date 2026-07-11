"""Turns a provider's sync state into a confidence signal. This is the one
place that reads `staleness_seconds`/`sync_status` (Phase 4's whole reason
for existing) and turns it into something forecast/aggregate responses can
actually use - the brief's "confidence must depend on staleness, missing
providers, conflicting providers" requirement, implemented once and reused
everywhere rather than re-derived ad hoc per endpoint.
"""

from enum import Enum
from typing import Optional

from app.config import settings
from app.models import ProviderBalance, SyncStatus


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def provider_confidence(balance: Optional[ProviderBalance]) -> tuple[ConfidenceLevel, str]:
    if balance is None:
        return ConfidenceLevel.LOW, "No synced data yet for this provider - treat as missing, not zero."

    if balance.sync_status == SyncStatus.FAILED:
        return (
            ConfidenceLevel.LOW,
            f"Last sync attempt failed; showing the last confirmed value from {balance.source_updated_at.isoformat()}.",
        )
    if balance.sync_status == SyncStatus.CONFLICTING:
        return (
            ConfidenceLevel.LOW,
            "This provider's balance does not reconcile with its own recent transaction history - treat with caution.",
        )
    if balance.sync_status == SyncStatus.DELAYED or balance.staleness_seconds > settings.sync_stale_after_seconds:
        return (
            ConfidenceLevel.LOW,
            f"Data is {balance.staleness_seconds:.0f}s old, past the {settings.sync_stale_after_seconds:.0f}s freshness threshold.",
        )
    if balance.staleness_seconds > settings.sync_stale_after_seconds * 0.5:
        return ConfidenceLevel.MEDIUM, f"Data is {balance.staleness_seconds:.0f}s old - within tolerance but not fresh."

    return ConfidenceLevel.HIGH, "Recently synced and internally consistent."


_SEVERITY = {ConfidenceLevel.LOW: 0, ConfidenceLevel.MEDIUM: 1, ConfidenceLevel.HIGH: 2}


def weakest(*levels: ConfidenceLevel) -> ConfidenceLevel:
    """A combined signal (e.g. cash, which depends on all three providers)
    is only as trustworthy as its least trustworthy input."""
    return min(levels, key=lambda level: _SEVERITY[level])

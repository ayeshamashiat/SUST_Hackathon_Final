"""Static, documented alert -> stakeholder routing table.

Explicit and auditable rather than implicit: every alert category maps to a
named role in the operations hierarchy described in the brief (Section 5).
Provider-specific roles are kept provider-scoped (e.g. "bKash Operations
Team") to avoid ever implying one provider's team owns another provider's
case.
"""

from typing import Optional

from app.models.models import AlertCategory


def _routing_key(category: AlertCategory, provider_id: Optional[str]) -> str:
    if category == AlertCategory.LIQUIDITY:
        return "LIQUIDITY_CASH" if provider_id is None else "LIQUIDITY_PROVIDER"
    if category == AlertCategory.ANOMALY:
        return "ANOMALY_VELOCITY"
    return "DATA_QUALITY"


_ROUTING_TABLE = {
    "LIQUIDITY_CASH": {
        "owner_role": "field_officer",
        "role": "Field Officer",
        "owner": "Field Officer (on duty)",
        "action": "Arrange additional physical cash for this outlet before the projected shortage time.",
    },
    "LIQUIDITY_PROVIDER": {
        "owner_role": "field_officer",
        "role": "Field Officer",
        "owner": "{provider} Field Officer (on duty)",
        "action": "Coordinate an approved provider-specific float support request with {provider} Operations.",
    },
    "ANOMALY_VELOCITY": {
        "owner_role": "provider_ops",
        "role": "Provider Operations",
        "owner": "{provider} Operations Team",
        "action": (
            "Review the flagged transactions before approving any large cash replenishment; "
            "escalate to Risk/Compliance if the pattern continues."
        ),
    },
    "DATA_QUALITY": {
        "owner_role": "provider_ops",
        "role": "Provider Operations",
        "owner": "{provider} Operations Team",
        "action": "Confirm the data feed with {provider}'s technical team; do not act on this estimate until the feed is healthy again.",
    },
}


def get_routing(category: AlertCategory, provider_id: Optional[str], provider_name: Optional[str]) -> dict:
    key = _routing_key(category, provider_id)
    entry = _ROUTING_TABLE[key]
    label = provider_name or "the provider"
    return {
        "owner_role": entry["owner_role"],
        "role": entry["role"],
        "owner": entry["owner"].format(provider=label),
        "action": entry["action"].format(provider=label),
    }

"""Per-agent simulation bias configuration.

Three agents are seeded, each illustrating a distinct demonstration scenario
from the challenge brief (Section 11) using the same generic generator code -
the scenarios are data/parameters, not special-cased logic:

- ``zindabazar``: heavy, bKash-dominated cash-out during "Eid rush" -> drains
  the *shared cash reserve* fastest (Scenario A/B: cash shortage attributed
  mostly to one provider's cash-out demand). Also the agent that receives
  periodic near-identical-amount bursts from a small customer pool, so the
  velocity anomaly detector has something real to catch.
- ``shahjalal``: heavy Rocket cash-in demand. Total balances look healthy,
  but Rocket's own e-money balance is quietly draining -> "hidden provider
  shortage" (Scenario A).
- ``amberkhana``: balanced, low-volume, mixed traffic -> should stay quiet,
  proving the system does not cry wolf on ordinary activity.
"""

from dataclasses import dataclass, field

PROVIDERS: list[tuple[str, str, str]] = [
    # (id, display name, color)
    ("bkash", "bKash", "#E2136E"),
    ("nagad", "Nagad", "#F6921E"),
    ("rocket", "Rocket", "#6C2EB9"),
]


@dataclass
class ProviderMix:
    provider_id: str
    weight: float


@dataclass
class AgentProfile:
    agent_id: str
    name: str
    area: str
    cash_start: float
    provider_balance_start: dict[str, float]
    cash_out_share: float  # probability a generated tx is CASH_OUT vs CASH_IN
    cash_out_mix: list[ProviderMix]
    cash_in_mix: list[ProviderMix]
    tx_per_tick_range: tuple[int, int]
    amount_range: tuple[float, float]
    burst_enabled: bool = False
    burst_provider: str = "bkash"
    burst_customer_pool: list[str] = field(default_factory=list)
    burst_amount_range: tuple[float, float] = (4_950.0, 5_050.0)
    burst_every_ticks_range: tuple[int, int] = (18, 30)
    burst_size_range: tuple[int, int] = (6, 9)
    burst_start_after_minutes: float = 0.0  # delay so the detector sees a clean baseline first


AGENT_PROFILES: dict[str, AgentProfile] = {
    "zindabazar": AgentProfile(
        agent_id="zindabazar",
        name="Zindabazar Bazar Corner",
        area="Zindabazar",
        cash_start=18_000.0,
        provider_balance_start={"bkash": 40_000.0, "nagad": 35_000.0, "rocket": 30_000.0},
        # Organic mix is only mildly bKash-leaning; the periodic burst below
        # is what makes bKash dominate both the cash-drain attribution *and*
        # the anomaly detector - the same root cause shows up in both signals,
        # which is intentional (a coherent story, not a coincidence).
        cash_out_share=0.85,
        cash_out_mix=[ProviderMix("bkash", 0.4), ProviderMix("nagad", 0.35), ProviderMix("rocket", 0.25)],
        cash_in_mix=[ProviderMix("bkash", 0.4), ProviderMix("nagad", 0.3), ProviderMix("rocket", 0.3)],
        tx_per_tick_range=(1, 2),
        amount_range=(500.0, 4_000.0),
        burst_enabled=True,
        burst_provider="bkash",
        burst_customer_pool=["CUST-1042", "CUST-1088", "CUST-1117"],
        burst_every_ticks_range=(12, 18),
        burst_size_range=(9, 13),
        burst_start_after_minutes=8.0,
    ),
    "shahjalal": AgentProfile(
        agent_id="shahjalal",
        name="Shahjalal Uposhohor Outlet",
        area="Uposhohor",
        cash_start=70_000.0,
        provider_balance_start={"bkash": 50_000.0, "nagad": 45_000.0, "rocket": 12_000.0},
        cash_out_share=0.35,
        cash_out_mix=[ProviderMix("bkash", 0.4), ProviderMix("nagad", 0.4), ProviderMix("rocket", 0.2)],
        cash_in_mix=[ProviderMix("rocket", 0.7), ProviderMix("bkash", 0.15), ProviderMix("nagad", 0.15)],
        tx_per_tick_range=(1, 2),
        amount_range=(500.0, 3_500.0),
    ),
    "amberkhana": AgentProfile(
        agent_id="amberkhana",
        name="Amberkhana Point",
        area="Amberkhana",
        cash_start=60_000.0,
        provider_balance_start={"bkash": 40_000.0, "nagad": 40_000.0, "rocket": 40_000.0},
        cash_out_share=0.5,
        cash_out_mix=[ProviderMix("bkash", 0.34), ProviderMix("nagad", 0.33), ProviderMix("rocket", 0.33)],
        cash_in_mix=[ProviderMix("bkash", 0.34), ProviderMix("nagad", 0.33), ProviderMix("rocket", 0.33)],
        tx_per_tick_range=(0, 1),
        amount_range=(300.0, 2_000.0),
    ),
}

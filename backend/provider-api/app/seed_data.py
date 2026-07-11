"""Static seed identities, shared by the seed script here and (later) by
aggregator-api when it seeds the matching Agent rows in shared_db - kept as
plain data in one place so both sides stay in sync without importing across
service boundaries.

15 synthetic "super agents" (registered across all three providers), named
after real Sylhet-area market/neighborhood names for demo realism. No real
customer or account data anywhere in this list.
"""

AGENTS: list[tuple[str, str, str]] = [
    ("agent-001", "Zindabazar Bazar Corner", "Zindabazar"),
    ("agent-002", "Shahjalal Uposhohor Outlet", "Uposhohor"),
    ("agent-003", "Amberkhana Point", "Amberkhana"),
    ("agent-004", "Bandar Bazar Trading", "Bandar Bazar"),
    ("agent-005", "Kumarpara Mobile Banking", "Kumarpara"),
    ("agent-006", "Mirabazar Service Center", "Mirabazar"),
    ("agent-007", "Chowhatta Corner Shop", "Chowhatta"),
    ("agent-008", "Tilagor Junction Outlet", "Tilagor"),
    ("agent-009", "Shibganj Bazar Stall", "Shibganj"),
    ("agent-010", "Modina Market Booth", "Modina Market"),
    ("agent-011", "Court Point Agent Shop", "Court Point"),
    ("agent-012", "Subid Bazar Outlet", "Subid Bazar"),
    ("agent-013", "Rikabibazar Service Point", "Rikabibazar"),
    ("agent-014", "Lamabazar Corner Store", "Lamabazar"),
    ("agent-015", "Naiorpul Mobile Point", "Naiorpul"),
]

PROVIDERS: list[str] = ["bkash", "nagad", "rocket"]

# (min, max) opening e-money balance per provider - deliberately different
# ranges so "each provider has a different balance" holds even before any
# transaction history is generated.
PROVIDER_OPENING_BALANCE_RANGE: dict[str, tuple[float, float]] = {
    "bkash": (30_000.0, 60_000.0),
    "nagad": (20_000.0, 45_000.0),
    "rocket": (10_000.0, 35_000.0),
}

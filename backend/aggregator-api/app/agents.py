"""Static demo reference data shared across this service.

Mirrors provider-api/app/seed_data.py's agent list and frontend/src/lib/
agents.ts's provider labels - kept as a small local copy rather than a
cross-service import (independently deployable services share a data
contract, not Python code), but consolidated here so auth/seed.py and
cases/routing.py don't each keep their own duplicate.
"""

AGENT_IDS = [f"agent-{i:03d}" for i in range(1, 16)]

PROVIDER_DISPLAY_NAME = {"bkash": "bKash", "nagad": "Nagad", "rocket": "Rocket"}

PROVIDER_DISPLAY_NAME_BN = {"bkash": "বিকাশ", "nagad": "নগদ", "rocket": "রকেট"}

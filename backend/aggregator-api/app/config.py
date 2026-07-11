from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    shared_database_url: str

    # Reads the SAME env var sync-service uses (SYNC_STALE_AFTER_SECONDS) -
    # confidence scoring here is meaningless if it disagrees with the value
    # that actually decided a row's sync_status, so this deliberately isn't
    # a second, independently-tunable constant.
    sync_stale_after_seconds: float = 60.0

    # Optional: services/llm.py falls back to a deterministic recommendation
    # whenever this is blank, so it is never required for alerts to work.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"


settings = Settings()


# --- Cash-balance modeling assumption -------------------------------------
# No component in this system generates or stores a physical-cash figure
# anywhere (Phase 3's simulator only ever writes provider e-money
# transactions; "shared_db is a read-only projection written only by
# sync-service" per Phase 4 means aggregator-api cannot write one either).
# Cash is therefore DERIVED here, read-only, from the same transaction
# projection already available: every CASH_OUT decreases physical cash
# (agent hands cash to the customer) and increases that provider's e-money
# balance; CASH_IN is the reverse - the same coupling already established in
# provider-api's models/seed/simulator. A single opening balance is assumed
# per agent since there is no real per-agent starting-cash source yet; this
# is a documented limitation, not a hidden guess.
CASH_OPENING_BALANCE = 80_000.0

# --- Forecast tuning (ported from the earlier single-service prototype's
# analytics/forecaster.py - same reasoning, adapted to shared_db) ----------
FORECAST_LOOKBACK_MINUTES = 45
FORECAST_MIN_SAMPLES = 5
FORECAST_MIN_WINDOW_MINUTES = 3.0
FORECAST_HIGH_CONFIDENCE_SAMPLES = 10
FORECAST_ALERT_HORIZON_MINUTES = 180
SIGNIFICANCE_Z_THRESHOLD = 1.5
CASH_SAFETY_THRESHOLD = 5_000.0
PROVIDER_SAFETY_THRESHOLD = 5_000.0

# --- Anomaly detector tuning -----------------------------------------------
ANOMALY_WINDOW_MINUTES = 6.0
ANOMALY_BASELINE_MINUTES = 60.0
ANOMALY_MIN_WINDOW_COUNT = 5
ANOMALY_MIN_BASELINE_COUNT = 10
ANOMALY_MIN_HISTORY_MINUTES = 12.0
ANOMALY_Z_THRESHOLD = 2.0
# unique_customers / window_count at or below this = accounts are repeating,
# not diverse - this is what tells a real Eid spike (diverse accounts, high
# concentration ratio near 1.0) apart from an injected burst (few repeating
# accounts, ratio near 0).
ANOMALY_CONCENTRATION_THRESHOLD = 0.5

# --- Per-agent historical amount-outlier tuning -----------------------------
# Separate from the velocity/clustering detector above: that one catches
# BURSTS (many transactions in a short window). This one catches a single
# transaction whose AMOUNT is unusual for what this specific agent normally
# does, even in isolation - e.g. an agent whose typical cash-out is
# 500-2,000 BDT suddenly processing 50,000. Needs real historical depth
# (see provider-api/app/historical_seed.py) to mean anything; with only a
# handful of transactions "unusual for this agent" isn't a meaningful
# statement yet, which is exactly what HISTORICAL_MIN_SAMPLES guards.
HISTORICAL_LOOKBACK_DAYS = 30.0
HISTORICAL_MIN_SAMPLES = 20  # minimum prior same-type transactions before trusting a mean/stdev for this agent
HISTORICAL_Z_THRESHOLD = 3.0  # how many of the agent's own historical standard deviations away counts as an outlier

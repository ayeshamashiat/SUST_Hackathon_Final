from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    shared_database_url: str

    # aggregator-api's own database (users, alerts, cases) - separate from
    # shared_database_url above, which is read-only. See db-init/
    # init-databases.sh for why these are deliberately two different
    # credentials against two different databases.
    aggregator_database_url: str

    # Reads the SAME env var sync-service uses (SYNC_STALE_AFTER_SECONDS) -
    # confidence scoring here is meaningless if it disagrees with the value
    # that actually decided a row's sync_status, so this deliberately isn't
    # a second, independently-tunable constant.
    sync_stale_after_seconds: float = 60.0

    # --- Auth ---
    # Dev-only default; override via env var for any non-local deployment.
    jwt_secret_key: str = "dev-insecure-secret-change-me-before-any-real-deployment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    demo_login_code: str = "Passw0rd!"

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

# --- Alert engine (Phase 7: assignment + case lifecycle) ------------------
# How often the background loop re-evaluates every agent's forecast/anomaly
# signals into Alert rows - same pattern as sync-service's own poll loop.
ALERT_EVAL_INTERVAL_SECONDS = 20.0
# Don't create a duplicate alert for the same agent+provider+type+metric
# while a prior one for the same thing is still open (anything short of
# CLOSED) and within this cooldown window.
ALERT_REOPEN_COOLDOWN_MINUTES = 15.0
# Liquidity severity thresholds - reuses the same minutes-to-shortage
# breakpoints as the forecast horizon, so "High liquidity" in the assignment
# rules means the same thing as an urgent forecast everywhere else.
LIQUIDITY_HIGH_SEVERITY_MINUTES = 30.0
LIQUIDITY_MEDIUM_SEVERITY_MINUTES = 90.0

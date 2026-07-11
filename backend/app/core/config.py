"""Central tunables for the simulation and analytics engines.

Kept in one place so the numbers behind a live demo (tick rate, thresholds,
lookback windows) are easy to find and explain to judges.
"""

DATABASE_URL = "sqlite:///./sust_hackathon.db"

# --- Simulation ---
TICK_SECONDS = 4.0
CASH_SAFETY_THRESHOLD = 5_000.0
PROVIDER_SAFETY_THRESHOLD = 5_000.0

# --- Forecaster ---
FORECAST_LOOKBACK_MINUTES = 45
FORECAST_MIN_SAMPLES = 5
FORECAST_MIN_WINDOW_MINUTES = 3.0  # guards against extrapolating from a few noisy seconds
FORECAST_HIGH_CONFIDENCE_SAMPLES = 10
FORECAST_ALERT_HORIZON_MINUTES = 180
SIGNIFICANCE_Z_THRESHOLD = 1.5  # min z-score before a downward drift is treated as a real trend, not noise

# --- Anomaly detector (velocity spike) ---
VELOCITY_WINDOW_MINUTES = 6
VELOCITY_BASELINE_MINUTES = 60
VELOCITY_MIN_WINDOW_COUNT = 5
VELOCITY_MIN_BASELINE_COUNT = 10  # cold-start guard: don't claim a spike with no real baseline yet
VELOCITY_MIN_HISTORY_MINUTES = 12  # need a baseline period at least 2x the window to be meaningful
VELOCITY_Z_SCORE_THRESHOLD = 2.0

# --- Data feed staleness ---
FEED_STALE_AFTER_SECONDS = 90

# --- Alert de-duplication ---
ALERT_REOPEN_COOLDOWN_MINUTES = 10

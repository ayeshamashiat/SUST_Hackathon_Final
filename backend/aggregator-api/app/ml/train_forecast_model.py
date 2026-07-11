"""Offline training script for the liquidity forecasting model - additive
to (never a replacement for) the statistical trend detector in
services/forecast.py; this only supplies a second, ML-based number that
services/alerts.py surfaces alongside the existing rule-based evidence.

Usage (container already running):
    docker compose exec aggregator-api python -m app.ml.train_forecast_model

Trains on every agent's full transaction history in shared_db - read-only,
matching aggregator-api's SELECT-only Postgres role (see db.py); this
script never writes to the database. Saves the model + metadata under
app/ml/models/, a mounted volume (see docker-compose.yml) so a retrain
survives container restarts and rebuilds. Re-running is safe: it always
retrains from the current full history and overwrites the previous artifact.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sqlmodel import select

from app.db import shared_session
from app.ml.features import CATEGORICAL_FEATURES, FEATURE_COLUMNS, TARGET_COLUMN, build_training_frame
from app.models import TransactionProjection

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "forecast_model.joblib"
METADATA_PATH = MODEL_DIR / "forecast_model.json"

# Held out by TIME, not randomly - the most recent slice of each agent's
# timeline, so evaluation reflects forecasting the future from the past,
# never training on data that is chronologically after the test window.
TEST_FRACTION = 0.15


def _time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.sort_values("bucket_start")
    cutoff = df["bucket_start"].quantile(1 - TEST_FRACTION)
    return df[df["bucket_start"] < cutoff], df[df["bucket_start"] >= cutoff]


def main() -> None:
    with shared_session() as session:
        agent_ids = sorted(row for row in session.exec(select(TransactionProjection.agent_id).distinct()))
        print(f"Building training frame for {len(agent_ids)} agent(s)...")
        df = build_training_frame(session, agent_ids)

    if df.empty:
        print("No transaction history found in shared_db - run provider-api's seed/historical_seed first.")
        return

    train_df, test_df = _time_split(df)
    print(f"{len(train_df)} training rows, {len(test_df)} held-out (time-based) test rows")

    model = HistGradientBoostingRegressor(categorical_features=CATEGORICAL_FEATURES, random_state=42)
    model.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])

    predictions = model.predict(test_df[FEATURE_COLUMNS])
    mae = mean_absolute_error(test_df[TARGET_COLUMN], predictions)
    naive_mae = mean_absolute_error(test_df[TARGET_COLUMN], test_df["lag_1"])
    print(f"Model MAE:   {mae:.2f} BDT/bucket")
    print(f"Naive MAE:   {naive_mae:.2f} BDT/bucket (persistence baseline: predict last bucket's flow)")
    if naive_mae:
        print(f"Improvement: {(1 - mae / naive_mae) * 100:.1f}% vs. naive baseline")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METADATA_PATH.write_text(
        json.dumps(
            {
                "trained_at": datetime.now(timezone.utc).isoformat(),
                "feature_columns": FEATURE_COLUMNS,
                "training_rows": len(train_df),
                "test_rows": len(test_df),
                "test_mae": mae,
                "naive_mae": naive_mae,
            },
            indent=2,
        )
    )
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()

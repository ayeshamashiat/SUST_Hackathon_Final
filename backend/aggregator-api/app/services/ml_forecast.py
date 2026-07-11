"""Loads the trained liquidity forecasting model
(app/ml/train_forecast_model.py) and produces a second, ML-based
burn-rate/ETA prediction - purely additive to services/forecast.py's
statistical trend detector, which remains the sole source of the
AT_RISK/STABLE decision and of everything shown when this model is
unavailable.

Returns None wherever the model hasn't been trained yet (no artifact on
disk) or there isn't enough recent history for a prediction - so nothing
here can block or change whether an alert gets generated.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from sqlmodel import Session

from app.ml.features import BUCKET_MINUTES, FEATURE_COLUMNS, latest_feature_row

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "models" / "forecast_model.joblib"

_model = None
_load_attempted = False


def _get_model():
    global _model, _load_attempted
    if _load_attempted:
        return _model
    _load_attempted = True
    if not MODEL_PATH.exists():
        return None
    _model = joblib.load(MODEL_PATH)
    return _model


@dataclass
class MLForecast:
    predicted_net_flow_next_bucket: float
    predicted_burn_rate_per_minute: float
    predicted_minutes_to_shortage: Optional[float]


def predict(
    session: Session,
    agent_id: str,
    target: str,
    current_balance: float,
    threshold: float,
    now: Optional[datetime] = None,
) -> Optional[MLForecast]:
    model = _get_model()
    if model is None:
        return None

    row = latest_feature_row(session, agent_id, target, now=now)
    if row is None:
        return None

    frame = pd.DataFrame([row])[FEATURE_COLUMNS]
    predicted_net_flow = float(model.predict(frame)[0])
    predicted_rate = predicted_net_flow / BUCKET_MINUTES

    minutes_to_shortage = None
    if predicted_rate < 0:
        minutes_to_shortage = max((current_balance - threshold) / abs(predicted_rate), 0.0)

    return MLForecast(
        predicted_net_flow_next_bucket=round(predicted_net_flow, 2),
        predicted_burn_rate_per_minute=round(predicted_rate, 2),
        predicted_minutes_to_shortage=round(minutes_to_shortage, 1) if minutes_to_shortage is not None else None,
    )

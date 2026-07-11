"""Feature engineering shared between offline training
(train_forecast_model.py) and online inference (services/ml_forecast.py) -
kept in one place so a trained model and the features fed to it at
prediction time can never silently drift apart.

Buckets each agent+target's transaction history into fixed-width intervals
and predicts a bucket's net cash flow from that bucket's calendar features
(hour-of-day, weekend - always known in advance) plus lag features of the
buckets before it: a standard pooled one-step-ahead time-series setup,
additive to (not a replacement for) the statistical trend detector in
services/forecast.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from math import cos, pi, sin
from typing import Optional

import pandas as pd
from sqlmodel import Session, select

from app.models import TransactionProjection
from app.services.cash import PROVIDERS
from app.services.forecast import _signed_delta

BUCKET_MINUTES = 15
LAG_BUCKETS_SHORT = 4  # last 1 hour
LAG_BUCKETS_LONG = 96  # last 24 hours
TARGETS = ("CASH",) + PROVIDERS

FEATURE_COLUMNS = [
    "hour_sin",
    "hour_cos",
    "is_weekend",
    "lag_1",
    "lag_short_sum",
    "lag_long_sum",
    "agent_id",
    "target",
]
CATEGORICAL_FEATURES = ["agent_id", "target"]
TARGET_COLUMN = "net_flow"


def _calendar_features(ts: pd.Series) -> pd.DataFrame:
    hour = ts.dt.hour + ts.dt.minute / 60.0
    angle = 2 * pi * hour / 24.0
    return pd.DataFrame(
        {
            "hour_sin": angle.apply(sin),
            "hour_cos": angle.apply(cos),
            # Bangladesh weekend is Friday/Saturday (weekday 4, 5) - matches
            # provider-api/app/historical_seed.py's own weekend convention.
            "is_weekend": ts.dt.weekday.isin([4, 5]).astype(int),
        }
    )


def _bucketed_series(rows: list[TransactionProjection], target: str, start: datetime, end: datetime) -> pd.DataFrame:
    """One row per BUCKET_MINUTES interval in [start, end); net_flow = 0 for buckets with no transactions."""
    target_is_cash = target == "CASH"
    relevant = rows if target_is_cash else [r for r in rows if r.provider == target]

    buckets = pd.date_range(start=start, end=end, freq=f"{BUCKET_MINUTES}min", inclusive="left")
    net = pd.Series(0.0, index=buckets)
    for tx in relevant:
        delta = _signed_delta(tx, target_is_cash=target_is_cash)
        offset = (tx.occurred_at - start) // timedelta(minutes=BUCKET_MINUTES)
        bucket_start = start + offset * timedelta(minutes=BUCKET_MINUTES)
        if bucket_start in net.index:
            net.loc[bucket_start] += delta

    df = pd.DataFrame({"bucket_start": buckets, "net_flow": net.values})
    df["lag_1"] = df["net_flow"].shift(1)
    df["lag_short_sum"] = df["net_flow"].rolling(LAG_BUCKETS_SHORT).sum().shift(1)
    df["lag_long_sum"] = df["net_flow"].rolling(LAG_BUCKETS_LONG).sum().shift(1)
    df = pd.concat([df, _calendar_features(df["bucket_start"])], axis=1)
    df["target"] = target
    return df


def build_training_frame(session: Session, agent_ids: list[str]) -> pd.DataFrame:
    """Pulls every agent's full transaction history and returns one row per
    (agent, target, bucket) with features + that bucket's net_flow as the
    label, dropping rows without enough lag history yet."""
    frames = []
    for agent_id in agent_ids:
        rows = list(
            session.exec(
                select(TransactionProjection)
                .where(TransactionProjection.agent_id == agent_id)
                .order_by(TransactionProjection.occurred_at)
            )
        )
        if not rows:
            continue
        start = rows[0].occurred_at.replace(minute=0, second=0, microsecond=0)
        end = rows[-1].occurred_at + timedelta(minutes=BUCKET_MINUTES)

        for target in TARGETS:
            df = _bucketed_series(rows, target, start, end)
            df["agent_id"] = agent_id
            frames.append(df)

    if not frames:
        return pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN, "bucket_start"])

    full = pd.concat(frames, ignore_index=True)
    return full.dropna(subset=["lag_1", "lag_short_sum", "lag_long_sum"])


def latest_feature_row(session: Session, agent_id: str, target: str, now: Optional[datetime] = None) -> Optional[dict]:
    """Builds the single most recent feature row for online inference - same
    bucketing/lag logic as training, evaluated up to `now`. Returns None if
    there isn't yet enough history for the full lag window (mirrors
    services/forecast.py's INSUFFICIENT_DATA guard, just for this model)."""
    now = now or datetime.utcnow()
    lookback_start = now - timedelta(minutes=BUCKET_MINUTES * (LAG_BUCKETS_LONG + 2))

    target_is_cash = target == "CASH"
    stmt = select(TransactionProjection).where(
        TransactionProjection.agent_id == agent_id, TransactionProjection.occurred_at >= lookback_start
    )
    if not target_is_cash:
        stmt = stmt.where(TransactionProjection.provider == target)
    rows = list(session.exec(stmt.order_by(TransactionProjection.occurred_at)))

    offset = (now - lookback_start) // timedelta(minutes=BUCKET_MINUTES)
    bucket_start_of_now = lookback_start + offset * timedelta(minutes=BUCKET_MINUTES)
    df = _bucketed_series(rows, target, lookback_start, bucket_start_of_now + timedelta(minutes=BUCKET_MINUTES))
    if df.empty:
        return None
    last = df.iloc[-1]
    if last[["lag_1", "lag_short_sum", "lag_long_sum"]].isna().any():
        return None

    calendar = _calendar_features(pd.Series([now]))
    return {
        "hour_sin": float(calendar["hour_sin"].iloc[0]),
        "hour_cos": float(calendar["hour_cos"].iloc[0]),
        "is_weekend": int(calendar["is_weekend"].iloc[0]),
        "lag_1": float(last["lag_1"]),
        "lag_short_sum": float(last["lag_short_sum"]),
        "lag_long_sum": float(last["lag_long_sum"]),
        "agent_id": agent_id,
        "target": target,
    }

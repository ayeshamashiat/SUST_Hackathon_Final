"""AI-generated recommendation layer, additive to the existing rule-based
forecast/anomaly detectors (services/forecast.py, services/anomaly.py) -
this module never changes whether something is flagged, it only adds a
short natural-language recommendation alongside the deterministic evidence
and routing action already computed elsewhere.

Falls back to a deterministic recommendation whenever OPENAI_API_KEY is
unset or the API call fails, so alert generation is never blocked on an
external service being available or reachable.
"""

import json
from dataclasses import dataclass
from typing import Optional

from app.config import settings

_SYSTEM_PROMPT = (
    "You are a careful, advisory assistant supporting mobile financial service (MFS) "
    "agent-outlet liquidity and risk monitoring in Bangladesh. You are given evidence "
    "already computed by a deterministic statistical model; you have no access to raw "
    "transaction or customer data beyond what is given, and must not invent facts. "
    "Write a short recommendation (2-4 sentences, plain English) for the outlet's "
    "operations team.\n"
    "Rules:\n"
    "- Never use the words 'fraud', 'confirmed', or state a determination of wrongdoing - "
    "the evidence supports review, not a verdict.\n"
    "- Reference the specific numbers given rather than generic advice.\n"
    "- If the evidence signals low confidence or insufficient data, say so plainly and "
    "recommend gathering more data before acting."
)


@dataclass
class AIRecommendation:
    text: str
    source: str  # "ai" | "fallback"
    note: Optional[str] = None


_client = None
_client_init_attempted = False


def _get_client():
    global _client, _client_init_attempted
    if _client_init_attempted:
        return _client
    _client_init_attempted = True
    if not settings.openai_api_key:
        return None
    from openai import OpenAI  # deferred: optional dependency, only needed once a key is configured

    _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _call(user_prompt: str, fallback_text: str) -> AIRecommendation:
    client = _get_client()
    if client is None:
        return AIRecommendation(
            text=fallback_text,
            source="fallback",
            note="OPENAI_API_KEY not configured - showing rule-based recommendation.",
        )

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=220,
            temperature=0.3,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ValueError("empty response")
        return AIRecommendation(text=text, source="ai")
    except Exception as exc:  # noqa: BLE001 - any failure must fall back, never break alert generation
        return AIRecommendation(
            text=fallback_text,
            source="fallback",
            note=f"AI recommendation unavailable ({exc.__class__.__name__}) - showing rule-based recommendation.",
        )


def recommend_liquidity(agent_name: str, forecast_result, fallback_text: str, ml_prediction=None) -> AIRecommendation:
    evidence = {
        "agent": agent_name,
        "target": forecast_result.target_label,
        "status": forecast_result.status,
        "current_balance_bdt": round(forecast_result.current_balance, 2),
        "burn_rate_bdt_per_minute": (
            round(forecast_result.burn_rate_per_minute, 2) if forecast_result.burn_rate_per_minute is not None else None
        ),
        "minutes_to_projected_shortage": (
            round(forecast_result.minutes_to_shortage, 1) if forecast_result.minutes_to_shortage is not None else None
        ),
        "confidence": forecast_result.confidence.value,
        "confidence_note": forecast_result.confidence_note,
        "top_contributors": forecast_result.top_contributors,
    }
    # Additive second signal from app/ml/train_forecast_model.py, when a model
    # has been trained - the LLM may mention it, but it never overrides the
    # rule-based evidence above, which is what actually decided this is AT_RISK.
    if ml_prediction is not None:
        evidence["ml_model_prediction"] = {
            "predicted_burn_rate_bdt_per_minute": ml_prediction.predicted_burn_rate_per_minute,
            "predicted_minutes_to_shortage": ml_prediction.predicted_minutes_to_shortage,
        }
    prompt = (
        "Category: liquidity forecast (cash or e-money balance projected to run low).\n"
        f"Evidence (JSON): {json.dumps(evidence)}"
    )
    return _call(prompt, fallback_text)


def recommend_anomaly(agent_name: str, provider: str, anomaly_result, fallback_text: str) -> AIRecommendation:
    evidence = {
        "agent": agent_name,
        "provider": provider,
        "window_transaction_count": anomaly_result.window_count,
        "baseline_mean": round(anomaly_result.baseline_mean, 2),
        "baseline_stdev": round(anomaly_result.baseline_stdev, 2),
        "z_score": round(anomaly_result.z_score, 2) if anomaly_result.z_score is not None else None,
        "unique_customers_in_window": anomaly_result.unique_customers,
        "concentration_ratio": (
            round(anomaly_result.concentration_ratio, 2) if anomaly_result.concentration_ratio is not None else None
        ),
        "amount_range_bdt": [anomaly_result.amount_min, anomaly_result.amount_max],
        "confidence": anomaly_result.confidence.value,
    }
    prompt = (
        "Category: cash-out velocity/clustering anomaly (an unusual burst of activity, NOT a fraud determination).\n"
        f"Evidence (JSON): {json.dumps(evidence)}"
    )
    return _call(prompt, fallback_text)

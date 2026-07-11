"""Safe narrative abstraction for alert messages.

Mock mode is deterministic and evidence-backed. Live model access is not
implemented or enabled; it requires explicit user approval first.
"""

from dataclasses import dataclass

from app.alerts.templates import anomaly_messages, data_quality_messages, liquidity_messages
from app.analytics.forecaster import ForecastResult
from app.core.config import LLM_MODE


@dataclass(frozen=True)
class AlertNarrative:
    title: str
    english: str
    bangla: str
    banglish: str


def _require_mock_mode() -> None:
    if LLM_MODE != "mock":
        raise RuntimeError("Live LLM mode is disabled until explicit user approval is provided.")


def liquidity(agent_name: str, forecast: ForecastResult, provider_names: dict[str, str]) -> AlertNarrative:
    _require_mock_mode()
    title, english, bangla = liquidity_messages(agent_name, forecast, provider_names)
    eta = f"about {forecast.minutes_to_shortage:.0f} minutes" if forecast.minutes_to_shortage is not None else "an unknown time"
    banglish = (
        f"{agent_name}-er {forecast.target_label} {eta}-er moddhe komte pare. "
        f"Confidence: {forecast.confidence.value.lower()}. Safe next step: age theke support coordinate korun."
    )
    return AlertNarrative(title, english, bangla, banglish)


def anomaly(agent_name: str, provider_id: str, provider_name: str, result) -> AlertNarrative:
    _require_mock_mode()
    title, english, bangla = anomaly_messages(agent_name, provider_id, provider_name, result)
    banglish = (
        f"{agent_name}-e {provider_name}-er unusual cash-out pattern dekhha geche: "
        f"{result.window_count} transaction, {result.unique_customers} account. "
        "Eta fraud decision na; human review proyojon."
    )
    return AlertNarrative(title, english, bangla, banglish)


def data_quality(agent_name: str, provider_id: str, provider_name: str) -> AlertNarrative:
    _require_mock_mode()
    title, english, bangla = data_quality_messages(agent_name, provider_id, provider_name)
    banglish = (
        f"{agent_name}-er {provider_name} data feed late. Estimate-er confidence kom; "
        "feed thik na howa porjonto kono boro decision niben na."
    )
    return AlertNarrative(title, english, bangla, banglish)

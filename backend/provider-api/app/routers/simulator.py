from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from app.seed_data import AGENTS, PROVIDERS
from app.simulator import engine
from app.simulator.schemas import (
    FeedDelayIn,
    FeedDelayOut,
    InjectAnomalyIn,
    InjectAnomalyOut,
    SimulateRunIn,
    SimulateRunOut,
    SimulatorStatusOut,
)
from app.simulator.state import ScenarioState, state

router = APIRouter(prefix="/simulator", tags=["simulator"])

_AGENT_IDS = {agent_id for agent_id, _, _ in AGENTS}


def _validate_providers(providers: list[str]) -> None:
    unknown = set(providers) - set(PROVIDERS)
    if unknown:
        raise HTTPException(400, f"Unknown provider(s): {sorted(unknown)}. Valid: {PROVIDERS}")


def _validate_agents(agent_ids: list[str]) -> None:
    unknown = set(agent_ids) - _AGENT_IDS
    if unknown:
        raise HTTPException(400, f"Unknown agent_id(s): {sorted(unknown)}")


@router.post("/run", response_model=SimulateRunOut)
def run(body: SimulateRunIn):
    _validate_providers(body.providers)
    agent_ids = body.agent_ids or [a for a, _, _ in AGENTS]
    _validate_agents(agent_ids)

    default_count = 1 if body.mode == "normal" else engine.EID_DEFAULT_COUNT_PER_AGENT
    count = body.count if body.count is not None else default_count

    now = datetime.utcnow()
    generated_per_provider = {p: 0 for p in body.providers}
    for provider in body.providers:
        for agent_id in agent_ids:
            if body.mode == "eid_spike":
                created = engine.generate_eid_spike(provider, agent_id, count=count, multiplier=body.multiplier, now=now)
            else:
                created = engine.generate_normal(provider, agent_id, count=count, now=now)
            generated_per_provider[provider] += len(created)

    ambient_until = None
    if body.duration_minutes > 0:
        ambient_until = now + timedelta(minutes=body.duration_minutes)
        state.scenario = ScenarioState(mode=body.mode, multiplier=body.multiplier, until=ambient_until)

    return SimulateRunOut(
        mode=body.mode,
        generated_per_provider=generated_per_provider,
        total_generated=sum(generated_per_provider.values()),
        ambient_scenario_until=ambient_until,
    )


@router.post("/inject-anomaly", response_model=InjectAnomalyOut)
def inject_anomaly(body: InjectAnomalyIn):
    _validate_providers([body.provider])
    _validate_agents([body.agent_id])

    created = engine.generate_anomaly_burst(
        body.provider,
        body.agent_id,
        count=body.count,
        window_seconds=body.window_seconds,
        amount=body.amount,
        amount_jitter=body.amount_jitter,
        account_pool_size=body.account_pool_size,
    )
    return InjectAnomalyOut(
        provider=body.provider,
        agent_id=body.agent_id,
        transactions_created=len(created),
        window_seconds=body.window_seconds,
    )


@router.post("/feed-delay", response_model=FeedDelayOut)
def feed_delay(body: FeedDelayIn):
    _validate_providers([body.provider])

    if body.delay:
        state.paused_providers.add(body.provider)
    else:
        state.paused_providers.discard(body.provider)

    return FeedDelayOut(
        provider=body.provider,
        delayed=body.provider in state.paused_providers,
        paused_providers=sorted(state.paused_providers),
    )


@router.get("/status", response_model=SimulatorStatusOut)
def status():
    scenario = None
    if state.scenario.until and datetime.utcnow() < state.scenario.until:
        scenario = {
            "mode": state.scenario.mode,
            "multiplier": state.scenario.multiplier,
            "until": state.scenario.until,
        }

    return SimulatorStatusOut(
        running=state.running,
        started_at=state.started_at,
        last_tick_at=state.last_tick_at,
        paused_providers=sorted(state.paused_providers),
        ambient_scenario=scenario,
        transactions_generated=dict(state.tx_counts),
        last_anomaly_injected_at=dict(state.last_anomaly_injected_at),
    )

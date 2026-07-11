from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.alerts.templates import insufficient_data_message, liquidity_messages, stable_message
from app.analytics.forecaster import ForecastResult, forecast_cash, forecast_provider
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.models import Agent, CashDrawer, DataFeedStatus, Provider, ProviderBalance, Transaction, User, UserRole
from app.schemas.schemas import AgentBalancesOut, ForecastOut, ProviderBalanceOut

router = APIRouter(tags=["agents"])


def _has_user_context(user: object) -> bool:
    return isinstance(user, User)


def _require_agent_scope(user: User, agent_id: str) -> None:
    if not _has_user_context(user):
        return
    if user.role == UserRole.AGENT and agent_id != user.agent_id:
        raise HTTPException(403, "Not authorized to view this agent")


def _require_provider_scope(user: User, provider_id: Optional[str]) -> None:
    if not _has_user_context(user):
        return
    if user.role == UserRole.PROVIDER_OPS and provider_id is not None and provider_id != user.provider_id:
        raise HTTPException(403, "Not authorized to view this provider")


@router.get("/agents", response_model=list[Agent])
def list_agents(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if _has_user_context(current_user) and current_user.role == UserRole.AGENT:
        agent = session.get(Agent, current_user.agent_id)
        return [agent] if agent else []
    return list(session.exec(select(Agent)))


@router.get("/agents/{agent_id}/balances", response_model=AgentBalancesOut)
def get_balances(
    agent_id: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    _require_agent_scope(current_user, agent_id)
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")

    drawer = session.exec(select(CashDrawer).where(CashDrawer.agent_id == agent_id)).one()
    providers = list(session.exec(select(Provider)))
    if current_user.role == UserRole.PROVIDER_OPS:
        providers = [p for p in providers if p.id == current_user.provider_id]

    out_providers = []
    for provider in providers:
        bal = session.exec(
            select(ProviderBalance).where(
                ProviderBalance.agent_id == agent_id, ProviderBalance.provider_id == provider.id
            )
        ).one()
        feed = session.exec(
            select(DataFeedStatus).where(
                DataFeedStatus.agent_id == agent_id, DataFeedStatus.provider_id == provider.id
            )
        ).one()
        out_providers.append(
            ProviderBalanceOut(
                provider_id=provider.id,
                provider_name=provider.name,
                color=provider.color,
                balance=bal.balance,
                feed_health=feed.health,
                feed_last_update_at=feed.last_update_at,
            )
        )

    return AgentBalancesOut(
        agent_id=agent.id,
        agent_name=agent.name,
        area=agent.area,
        cash_balance=drawer.balance,
        cash_updated_at=drawer.updated_at,
        providers=out_providers,
    )


@router.get("/agents/{agent_id}/transactions", response_model=list[Transaction])
def get_transactions(
    agent_id: str,
    provider_id: Optional[str] = None,
    limit: Annotated[int, Query(le=500)] = 50,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _require_agent_scope(current_user, agent_id)
    if _has_user_context(current_user) and current_user.role == UserRole.PROVIDER_OPS:
        provider_id = provider_id or current_user.provider_id
        _require_provider_scope(current_user, provider_id)

    stmt = select(Transaction).where(Transaction.agent_id == agent_id)
    if provider_id:
        stmt = stmt.where(Transaction.provider_id == provider_id)
    stmt = stmt.order_by(Transaction.created_at.desc()).limit(limit)
    return list(session.exec(stmt))


@router.get("/agents/{agent_id}/forecast", response_model=list[ForecastOut])
def get_forecast(
    agent_id: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    _require_agent_scope(current_user, agent_id)
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")

    providers = list(session.exec(select(Provider)))
    provider_names = {p.id: p.name for p in providers}
    if current_user.role == UserRole.PROVIDER_OPS:
        providers = [p for p in providers if p.id == current_user.provider_id]

    results = [_to_forecast_out(agent.name, forecast_cash(session, agent_id), provider_names)]
    for provider in providers:
        results.append(_to_forecast_out(agent.name, forecast_provider(session, agent_id, provider.id), provider_names))
    return results


def _to_forecast_out(agent_name: str, forecast: ForecastResult, provider_names: dict[str, str]) -> ForecastOut:
    if forecast.status == "AT_RISK":
        title, message_en, message_bn = liquidity_messages(agent_name, forecast, provider_names)
    elif forecast.status == "STABLE":
        title = f"{forecast.target_label} is stable"
        message_en, message_bn = stable_message(forecast.target_label, forecast.target)
    else:
        title = f"{forecast.target_label}: insufficient data"
        message_en, message_bn = insufficient_data_message(forecast.target_label)

    return ForecastOut(
        target=forecast.target,
        target_label=forecast.target_label,
        status=forecast.status,
        current_balance=forecast.current_balance,
        burn_rate_per_minute=forecast.burn_rate_per_minute,
        projected_shortage_at=forecast.projected_shortage_at,
        minutes_to_shortage=forecast.minutes_to_shortage,
        confidence=forecast.confidence,
        confidence_note=forecast.confidence_note,
        data_quality=forecast.data_quality,
        top_contributors=forecast.top_contributors,
        message_en=message_en,
        message_bn=message_bn,
    )

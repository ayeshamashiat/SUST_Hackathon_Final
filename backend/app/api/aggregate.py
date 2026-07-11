"""Read-only aggregate views over the same simulator/forecast state."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.agents import _to_forecast_out
from app.analytics.forecaster import forecast_cash, forecast_provider
from app.core.database import get_session
from app.models.models import Agent, Provider
from app.schemas.schemas import AggregateForecastOut

router = APIRouter(prefix="/aggregate", tags=["aggregate"])


@router.get("/forecast", response_model=list[AggregateForecastOut])
def aggregate_forecast(session: Session = Depends(get_session)):
    providers = list(session.exec(select(Provider)))
    provider_names = {provider.id: provider.name for provider in providers}
    response = []
    for agent in session.exec(select(Agent)):
        forecasts = [_to_forecast_out(agent.name, forecast_cash(session, agent.id), provider_names)]
        forecasts.extend(
            _to_forecast_out(agent.name, forecast_provider(session, agent.id, provider.id), provider_names)
            for provider in providers
        )
        response.append(AggregateForecastOut(agent_id=agent.id, agent_name=agent.name, area=agent.area, forecasts=forecasts))
    return response

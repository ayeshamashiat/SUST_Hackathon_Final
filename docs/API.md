# API reference

## Core endpoints

- GET /health — liveness probe.
- GET /agents — list simulated agents.
- GET /agents/{agent_id}/balances — per-agent shared cash plus per-provider balances.
- GET /agents/{agent_id}/forecast — liquidity forecasts for the shared cash reserve and each provider.
- GET /agents/{agent_id}/transactions — recent transactions, optionally filtered by provider.
- GET /aggregate/forecast — combined forecast view for every agent and every provider.
- GET /alerts — alert feed with optional agent/provider/category filters.
- POST /alerts/{alert_id}/acknowledge — acknowledge an alert and advance the related case.
- POST /alerts/{alert_id}/escalate — escalate an alert and update the case owner.
- POST /alerts/{alert_id}/resolve — resolve the alert and related case.
- GET /metrics — operational proxy metrics for the demo.
- POST /simulation/seed — reseed the simulator data.
- POST /simulation/reset — reset the simulation state.
- POST /simulation/degrade-feed — freeze a provider feed for demonstration purposes.
- POST /simulate/scenario — run a named scenario.

## Metrics payload

The /metrics endpoint returns:

- sync_latency: placeholder proxy for feed synchronization delay.
- forecast_lead_time: placeholder proxy for how soon the forecast can issue a warning.
- anomaly_precision: precision of the anomaly detector against synthetic labels.
- recall: recall of the anomaly detector against synthetic labels.
- false_positive_rate: false-positive rate of the anomaly detector against synthetic labels.
- alert_explanation_coverage: proportion of alerts with both English and Bangla explanations.
- provider_sync_health: per-provider summary of configured feeds and tracked balances.

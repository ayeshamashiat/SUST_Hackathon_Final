# Commit Prompt

## Phase 6 — Alert Engine

Continue from the existing project. Alert Engine is an internal module inside Aggregator; do not create another service.

Implement automatic liquidity, anomaly, and data-quality alerts after synchronization. Route liquidity alerts to `field_officer`, anomaly and data-quality alerts to `provider_ops`, and escalations to `risk_analyst`.

Provide `GET /alerts` and alert lifecycle endpoints for acknowledge, escalate, and resolve. Every lifecycle action must create an `alert_event`.

Use `services/llm.py` only for alert narratives. Default to mock mode; do not enable a live API without explicit approval. Generate English, Bangla, and Banglish narratives without accusing users of fraud.

Document the lifecycle diagram, sample alerts, sample evidence, and owner routing.

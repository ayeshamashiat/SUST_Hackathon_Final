# Commit Prompt

## Phase 8 — What-if Simulator

Continue from the current architecture.

Add `POST /simulate/scenario` with provider, demand multiplier, duration, transaction rate, and cash-out ratio inputs.

Feed the request through simulator synchronization, forecasting, and alert generation without a shortcut. Effects must immediately appear in `GET /aggregate/forecast` and `GET /alerts`.

Provide example scenarios.

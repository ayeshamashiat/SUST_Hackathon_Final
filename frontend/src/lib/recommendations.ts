// Ranked recommendation engine: expands the backend's single
// recommended_action (cases/routing.py) into an ordered list of options per
// (alert type, current owner) - varies by stakeholder because who owns the
// case determines what's actually actionable for them right now. Scores are
// labeled "priority" deliberately, not "confidence" - they're a hand-authored
// ranking weight for ordering the list, not a statistical claim.
import type { AlertOut, AlertType, UserRole } from "./types";

export interface RankedAction {
  action: string;
  priority: number;
}

const TABLE: Partial<Record<AlertType, Partial<Record<UserRole, RankedAction[]>>>> = {
  LIQUIDITY: {
    AGENT: [
      { action: "Confirm your current cash / e-money balance", priority: 92 },
      { action: "Contact your Field Officer if the shortage looks real", priority: 85 },
      { action: "Continue monitoring", priority: 60 },
    ],
    FIELD_OFFICER: [
      { action: "Contact the agent immediately", priority: 95 },
      { action: "Verify cash availability at the outlet", priority: 92 },
      { action: "Continue monitoring before escalating", priority: 84 },
      { action: "Escalate to Provider Operations", priority: 68 },
    ],
    PROVIDER_OPS: [
      { action: "Coordinate an approved float / cash-replenishment request", priority: 94 },
      { action: "Check nearby outlet support options", priority: 78 },
      { action: "Continue monitoring", priority: 55 },
      { action: "Escalate to Risk / Compliance", priority: 40 },
    ],
    RISK_COMPLIANCE: [
      { action: "Confirm no unusual pattern is driving the shortage", priority: 88 },
      { action: "Clear the case for further operational support", priority: 75 },
      { action: "Escalate to Management", priority: 45 },
    ],
    MANAGEMENT: [
      { action: "Review recurring liquidity pressure at this outlet / area", priority: 80 },
      { action: "Close once outlet-level support channels are exhausted", priority: 60 },
    ],
  },
  ANOMALY: {
    RISK_COMPLIANCE: [
      { action: "Review the flagged transactions and evidence", priority: 93 },
      { action: "Examine repeated-account / amount evidence", priority: 88 },
      { action: "Request further review before any large replenishment", priority: 79 },
      { action: "Continue monitoring", priority: 55 },
    ],
    MANAGEMENT: [
      { action: "Monitor for recurrence across other agents / areas", priority: 82 },
      { action: "Close once Risk / Compliance review is complete", priority: 60 },
    ],
  },
  DATA_QUALITY: {
    PROVIDER_OPS: [
      { action: "Confirm the data feed with the provider's technical team", priority: 91 },
      { action: "Avoid acting on estimates from this feed until it's healthy", priority: 87 },
      { action: "Continue monitoring feed status", priority: 58 },
    ],
    RISK_COMPLIANCE: [
      { action: "Confirm whether this is technical or compliance-relevant", priority: 80 },
      { action: "Continue monitoring", priority: 55 },
    ],
    MANAGEMENT: [{ action: "Review this provider's integration health at the network level", priority: 75 }],
  },
};

const FALLBACK: RankedAction[] = [
  { action: "Review the evidence and decide: acknowledge, monitor, resolve, or escalate", priority: 70 },
];

export function rankedRecommendations(alert: AlertOut): RankedAction[] {
  return TABLE[alert.alert_type]?.[alert.current_owner] ?? FALLBACK;
}

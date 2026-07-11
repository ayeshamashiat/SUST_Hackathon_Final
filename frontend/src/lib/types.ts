export type FeedHealth = "OK" | "STALE" | "CONFLICTING";
export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";
export type DataQuality = "OK" | "DEGRADED";
export type ForecastStatus = "STABLE" | "AT_RISK" | "INSUFFICIENT_DATA";
export type CaseStatus = "NEW" | "ACKNOWLEDGED" | "IN_PROGRESS" | "ESCALATED" | "RESOLVED";
export type AlertCategory = "LIQUIDITY" | "ANOMALY" | "DATA_QUALITY";

export type UserRole = "AGENT" | "FIELD_OFFICER" | "AREA_MANAGER" | "PROVIDER_OPS" | "RISK_COMPLIANCE" | "MANAGEMENT";

export interface AuthUser {
  username: string;
  role: UserRole;
  display_name: string;
  agent_id: string | null;
  provider_id: string | null;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  role: UserRole;
  display_name: string;
  agent_id: string | null;
  provider_id: string | null;
}

export interface Agent {
  id: string;
  name: string;
  area: string;
}

export interface ProviderBalanceOut {
  provider_id: string;
  provider_name: string;
  color: string;
  balance: number;
  feed_health: FeedHealth;
  feed_last_update_at: string;
}

export interface AgentBalancesOut {
  agent_id: string;
  agent_name: string;
  area: string;
  cash_balance: number;
  cash_updated_at: string;
  providers: ProviderBalanceOut[];
}

export interface ForecastOut {
  target: string;
  target_label: string;
  status: ForecastStatus;
  current_balance: number;
  burn_rate_per_minute: number | null;
  projected_shortage_at: string | null;
  minutes_to_shortage: number | null;
  confidence: ConfidenceLevel;
  confidence_note: string;
  data_quality: DataQuality;
  top_contributors: { provider_id: string; amount: number; share: number }[];
  message_en: string;
  message_bn: string;
}

export interface CaseEventOut {
  id: number;
  event_type: string;
  note: string | null;
  actor: string;
  created_at: string;
}

export interface CaseOut {
  id: number;
  alert_id: number;
  stakeholder_role: string;
  owner: string;
  status: CaseStatus;
  recommended_action: string;
  created_at: string;
  updated_at: string;
  events: CaseEventOut[];
}

export interface AlertOut {
  id: number;
  category: AlertCategory;
  metric: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  agent_id: string;
  agent_name: string;
  provider_id: string | null;
  provider_name: string | null;
  title: string;
  message_en: string;
  message_bn: string;
  evidence: Record<string, unknown>;
  confidence: ConfidenceLevel;
  confidence_note: string;
  data_quality: DataQuality;
  created_at: string;
  case: CaseOut | null;
}

export interface Transaction {
  id: number;
  agent_id: string;
  provider_id: string;
  type: "CASH_IN" | "CASH_OUT";
  amount: number;
  customer_ref: string;
  area: string;
  status: "SUCCESS" | "FAILED";
  created_at: string;
}

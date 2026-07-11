// Auth types mirror backend/aggregator-api/app/schemas.py's TokenOut/UserOut
// and app/auth/models.py's UserRole. Data types mirror the rest of
// schemas.py - aggregator-api is the only backend service this frontend
// talks to. There is no /alerts or /cases endpoint yet (Phase 7, not built).

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

export interface UserOut {
  username: string;
  role: UserRole;
  display_name: string;
  agent_id: string | null;
  provider_id: string | null;
}

export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";
export type SyncStatus = "ok" | "delayed" | "failed" | "conflicting";
export type ForecastStatus = "STABLE" | "AT_RISK" | "INSUFFICIENT_DATA";

export interface Agent {
  id: string;
  name: string;
  area: string;
}

export interface ProviderBalanceOut {
  provider: string;
  balance: number | null;
  staleness_seconds: number | null;
  sync_status: SyncStatus | null;
  confidence: ConfidenceLevel;
  confidence_note: string;
}

export interface AgentAggregateOut {
  agent_id: string;
  cash_balance: number;
  cash_confidence: ConfidenceLevel;
  cash_confidence_note: string;
  providers: ProviderBalanceOut[];
  overall_confidence: ConfidenceLevel;
}

export interface TopContributor {
  provider: string;
  amount: number;
  share: number;
}

export interface ForecastOut {
  target: string; // "CASH" or a provider id
  target_label: string;
  status: ForecastStatus;
  current_balance: number;
  burn_rate_per_minute: number | null;
  projected_shortage_at: string | null;
  minutes_to_shortage: number | null;
  confidence: ConfidenceLevel;
  confidence_note: string;
  top_contributors: TopContributor[];
}

export interface AnomalyOut {
  agent_id: string;
  provider: string;
  flagged: boolean;
  window_count: number;
  baseline_mean: number;
  baseline_stdev: number;
  z_score: number | null;
  unique_customers: number;
  concentration_ratio: number | null;
  amount_min: number;
  amount_max: number;
  amount_coefficient_of_variation: number | null;
  sample_transaction_ids: number[];
  window_start: string | null;
  window_end: string | null;
  confidence: ConfidenceLevel;
  message: string;
}

export interface AmountOutlierOut {
  agent_id: string;
  provider: string;
  transaction_type: string;
  flagged: boolean;
  evaluated_transaction_id: number | null;
  evaluated_amount: number | null;
  evaluated_at: string | null;
  historical_sample_size: number;
  historical_mean: number | null;
  historical_stdev: number | null;
  z_score: number | null;
  confidence: ConfidenceLevel;
  message: string;
}

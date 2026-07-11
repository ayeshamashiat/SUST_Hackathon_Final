import { getToken } from "./authStorage";
import type {
  AgentAggregateOut,
  AlertOut,
  AmountOutlierOut,
  AnomalyOut,
  CaseStatus,
  ForecastOut,
  TokenOut,
  UserOut,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  login: async (username: string, password: string) => {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password }).toString(),
    });
    if (!res.ok) {
      throw new Error(res.status === 401 ? "Incorrect username or password" : `Login failed (${res.status})`);
    }
    return res.json() as Promise<TokenOut>;
  },
  me: () => request<UserOut>("/auth/me"),

  getAgentAggregate: (agentId: string) => request<AgentAggregateOut>(`/aggregate/agent/${agentId}`),
  getForecast: (agentId: string) => request<ForecastOut[]>(`/aggregate/forecast/${agentId}`),
  getAnomalies: (agentId: string, provider?: string) => {
    const search = provider ? `?provider=${provider}` : "";
    return request<AnomalyOut[]>(`/aggregate/anomaly/${agentId}${search}`);
  },
  getHistoricalOutliers: (agentId: string, provider?: string, transactionType: "cash_out" | "cash_in" = "cash_out") => {
    const search = new URLSearchParams({ transaction_type: transactionType });
    if (provider) search.set("provider", provider);
    return request<AmountOutlierOut[]>(`/aggregate/anomaly/${agentId}/historical?${search.toString()}`);
  },

  getAlerts: (filters: { agentId?: string; provider?: string; status?: CaseStatus } = {}) => {
    const search = new URLSearchParams();
    if (filters.agentId) search.set("agent_id", filters.agentId);
    if (filters.provider) search.set("provider", filters.provider);
    if (filters.status) search.set("status", filters.status);
    const qs = search.toString();
    return request<AlertOut[]>(`/alerts${qs ? `?${qs}` : ""}`);
  },
  getAlert: (alertId: number) => request<AlertOut>(`/alerts/${alertId}`),
  acknowledgeAlert: (alertId: number, note?: string) =>
    request<AlertOut>(`/alerts/${alertId}/acknowledge`, { method: "POST", body: JSON.stringify({ note }) }),
  startReview: (alertId: number, note?: string) =>
    request<AlertOut>(`/alerts/${alertId}/start-review`, { method: "POST", body: JSON.stringify({ note }) }),
  addCaseNote: (alertId: number, message: string) =>
    request<AlertOut>(`/alerts/${alertId}/notes`, { method: "POST", body: JSON.stringify({ message }) }),
  monitorAlert: (alertId: number, note?: string) =>
    request<AlertOut>(`/alerts/${alertId}/monitor`, { method: "POST", body: JSON.stringify({ note }) }),
  resolveAlert: (alertId: number, note?: string) =>
    request<AlertOut>(`/alerts/${alertId}/resolve`, { method: "POST", body: JSON.stringify({ note }) }),
  closeAlert: (alertId: number, note?: string) =>
    request<AlertOut>(`/alerts/${alertId}/close`, { method: "POST", body: JSON.stringify({ note }) }),
  escalateAlert: (alertId: number, reason: string) =>
    request<AlertOut>(`/alerts/${alertId}/escalate`, { method: "POST", body: JSON.stringify({ reason }) }),
};

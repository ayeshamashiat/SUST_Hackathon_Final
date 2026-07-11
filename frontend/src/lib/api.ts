import { getToken } from "./authStorage";
import type {
  Agent,
  AgentBalancesOut,
  AlertCategory,
  AlertOut,
  AuthUser,
  CaseOut,
  CaseStatus,
  ForecastOut,
  TokenOut,
  Transaction,
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
  me: () => request<AuthUser>("/auth/me"),
  listAgents: () => request<Agent[]>("/agents"),
  getBalances: (agentId: string) => request<AgentBalancesOut>(`/agents/${agentId}/balances`),
  getForecast: (agentId: string) => request<ForecastOut[]>(`/agents/${agentId}/forecast`),
  getTransactions: (agentId: string, limit = 25) =>
    request<Transaction[]>(`/agents/${agentId}/transactions?limit=${limit}`),
  listAlerts: (params: { agentId?: string; category?: AlertCategory; limit?: number } = {}) => {
    const search = new URLSearchParams();
    if (params.agentId) search.set("agent_id", params.agentId);
    if (params.category) search.set("category", params.category);
    search.set("limit", String(params.limit ?? 50));
    return request<AlertOut[]>(`/alerts?${search.toString()}`);
  },
  getAlert: (alertId: number) => request<AlertOut>(`/alerts/${alertId}`),
  updateCase: (caseId: number, body: { status?: CaseStatus; note?: string }) =>
    request<CaseOut>(`/cases/${caseId}`, { method: "PATCH", body: JSON.stringify(body) }),
  simulationStatus: () => request<{ running: boolean; agent_count: number; degraded_feeds: unknown[] }>(
    "/simulation/status"
  ),
  degradeFeed: (agentId: string, providerId: string, degrade: boolean) =>
    request<{ status: string }>("/simulation/degrade-feed", {
      method: "POST",
      body: JSON.stringify({ agent_id: agentId, provider_id: providerId, degrade }),
    }),
};

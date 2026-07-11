import type {
  Agent,
  AgentBalancesOut,
  AlertCategory,
  AlertOut,
  CaseOut,
  CaseStatus,
  ForecastOut,
  Transaction,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
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
  updateCase: (caseId: number, body: { status?: CaseStatus; note?: string; actor: string }) =>
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

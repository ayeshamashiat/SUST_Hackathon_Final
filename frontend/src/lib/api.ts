import { getToken } from "./authStorage";
import type { AgentAggregateOut, AmountOutlierOut, AnomalyOut, ForecastOut, TokenOut, UserOut } from "./types";

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
};

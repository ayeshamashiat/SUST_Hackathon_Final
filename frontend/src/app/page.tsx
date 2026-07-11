"use client";

import { useEffect, useState } from "react";
import { AgentSelector } from "@/components/AgentSelector";
import { BalanceCard } from "@/components/BalanceCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatBDT, formatRelative } from "@/lib/format";
import type { Agent, AgentBalancesOut, ForecastOut, Transaction } from "@/lib/types";

const POLL_MS = 4000;

export default function DashboardPage() {
  const { user } = useAuth();
  const isAgentRole = user?.role === "AGENT";
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(isAgentRole ? user!.agent_id : null);
  const [balances, setBalances] = useState<AgentBalancesOut | null>(null);
  const [forecasts, setForecasts] = useState<ForecastOut[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listAgents()
      .then((list) => {
        setAgents(list);
        setSelectedAgent((prev) => prev ?? list[0]?.id ?? null);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!selectedAgent) return;
    let cancelled = false;

    async function refresh() {
      try {
        const [b, f, t] = await Promise.all([
          api.getBalances(selectedAgent!),
          api.getForecast(selectedAgent!),
          api.getTransactions(selectedAgent!, 10),
        ]);
        if (!cancelled) {
          setBalances(b);
          setForecasts(f);
          setTransactions(t);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    }

    refresh();
    const interval = setInterval(refresh, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [selectedAgent]);

  const cashForecast = forecasts.find((f) => f.target === "CASH");
  const providerForecast = (providerId: string) => forecasts.find((f) => f.target === providerId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold mb-1">Unified outlet view</h1>
        <p className="text-sm text-slate-600">
          One shared cash drawer, three separate provider balances. Nothing here merges provider funds - it is a
          read-only combined view for decision support.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}). Is the backend running on port 8000?
        </div>
      )}

      {!isAgentRole && <AgentSelector agents={agents} selected={selectedAgent} onSelect={setSelectedAgent} />}

      {balances && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <BalanceCard
            label="Shared Cash Reserve"
            color="#22c55e"
            balance={balances.cash_balance}
            forecast={cashForecast}
          />
          {balances.providers.map((p) => (
            <BalanceCard
              key={p.provider_id}
              label={p.provider_name}
              color={p.color}
              balance={p.balance}
              feedHealth={p.feed_health}
              feedUpdatedAt={p.feed_last_update_at}
              forecast={providerForecast(p.provider_id)}
            />
          ))}
        </div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white">
        <div className="px-4 py-3 border-b border-slate-200 text-sm font-medium">Recent transactions</div>
        <div className="divide-y divide-slate-200 max-h-80 overflow-y-auto">
          {transactions.length === 0 && <div className="px-4 py-3 text-sm text-slate-500">No activity yet.</div>}
          {transactions.map((t) => (
            <div key={t.id} className="px-4 py-2.5 flex items-center justify-between text-sm">
              <div className="flex items-center gap-3">
                <span
                  className={`inline-flex w-16 justify-center rounded px-1.5 py-0.5 text-xs font-medium ${
                    t.type === "CASH_OUT" ? "bg-sky-100 text-sky-700" : "bg-fuchsia-100 text-fuchsia-700"
                  }`}
                >
                  {t.type === "CASH_OUT" ? "Cash-out" : "Cash-in"}
                </span>
                <span className="text-slate-600 uppercase text-xs">{t.provider_id}</span>
                <span className="text-slate-500 text-xs">{t.customer_ref}</span>
                {t.status === "FAILED" && (
                  <span className="rounded bg-rose-100 px-1.5 py-0.5 text-xs text-rose-700">
                    declined - insufficient balance
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3">
                <span className="tabular-nums">{formatBDT(t.amount)}</span>
                <span className="text-xs text-slate-500 w-14 text-right">{formatRelative(t.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

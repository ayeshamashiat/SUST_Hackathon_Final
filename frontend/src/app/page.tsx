"use client";

import { useEffect, useState } from "react";
import { AgentSelector } from "@/components/AgentSelector";
import { BalanceCard } from "@/components/BalanceCard";
import { ConfidenceBadge } from "@/components/Badges";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AGENTS, PROVIDER_COLOR, PROVIDER_LABEL, type ProviderId } from "@/lib/agents";
import type { AgentAggregateOut, ForecastOut } from "@/lib/types";

const POLL_MS = 5000;

export default function DashboardPage() {
  const { user } = useAuth();
  const isAgentRole = user?.role === "AGENT";
  const [selectedAgent, setSelectedAgent] = useState<string | null>(isAgentRole ? user!.agent_id : AGENTS[0]?.id ?? null);
  const [aggregate, setAggregate] = useState<AgentAggregateOut | null>(null);
  const [forecasts, setForecasts] = useState<ForecastOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedAgent) return;
    let cancelled = false;

    async function refresh() {
      try {
        const [agg, fc] = await Promise.all([api.getAgentAggregate(selectedAgent!), api.getForecast(selectedAgent!)]);
        if (!cancelled) {
          setAggregate(agg);
          setForecasts(fc);
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
  const providerForecast = (provider: string) => forecasts.find((f) => f.target === provider);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-extrabold mb-1 tracking-tight">Unified outlet view</h1>
        <p className="text-[13.5px] text-slate-500 max-w-[560px] leading-relaxed">
          One shared cash drawer, three separate provider balances. Cash is a derived, read-only figure computed
          from synced transaction history - not an authoritative provider balance, and nothing here merges provider
          funds.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}). Is aggregator-api running on port 8000?
        </div>
      )}

      {!isAgentRole && <AgentSelector agents={AGENTS} selected={selectedAgent} onSelect={setSelectedAgent} />}

      {aggregate && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <BalanceCard
              label="Shared Cash Reserve (derived)"
              color="#22c55e"
              balance={aggregate.cash_balance}
              forecast={cashForecast}
            />
            {aggregate.providers.map((p) => (
              <BalanceCard
                key={p.provider}
                label={PROVIDER_LABEL[p.provider as ProviderId] ?? p.provider}
                color={PROVIDER_COLOR[p.provider as ProviderId] ?? "#64748b"}
                balance={p.balance}
                syncStatus={p.sync_status}
                stalenessSeconds={p.staleness_seconds}
                forecast={providerForecast(p.provider)}
              />
            ))}
          </div>

          <div className="rounded-2xl border border-[#E8EAF0] bg-white px-4 py-3 flex items-center justify-between gap-4 text-sm">
            <span className="text-slate-600">Overall confidence for this agent</span>
            <ConfidenceBadge level={aggregate.overall_confidence} />
          </div>
        </>
      )}
    </div>
  );
}

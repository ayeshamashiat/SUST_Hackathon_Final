"use client";

import { useEffect, useState } from "react";
import { AlertCaseCard } from "@/components/AlertCaseCard";
import { BalanceCard } from "@/components/BalanceCard";
import { ConfidenceBadge } from "@/components/Badges";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PROVIDER_COLOR, PROVIDER_LABEL, type ProviderId } from "@/lib/agents";
import type { AgentAggregateOut, AlertOut, ForecastOut } from "@/lib/types";

const POLL_MS = 5000;

export default function AgentDashboard() {
  const { user } = useAuth();
  const agentId = user?.agent_id ?? null;
  const [aggregate, setAggregate] = useState<AgentAggregateOut | null>(null);
  const [forecasts, setForecasts] = useState<ForecastOut[]>([]);
  const [cases, setCases] = useState<AlertOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) return;
    let cancelled = false;

    async function refresh() {
      try {
        const [agg, fc, myCases] = await Promise.all([
          api.getAgentAggregate(agentId!),
          api.getForecast(agentId!),
          api.getAlerts({ agentId: agentId! }),
        ]);
        if (!cancelled) {
          setAggregate(agg);
          setForecasts(fc);
          setCases(myCases);
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
  }, [agentId]);

  const cashForecast = forecasts.find((f) => f.target === "CASH");
  const providerForecast = (provider: string) => forecasts.find((f) => f.target === provider);
  const openCases = cases.filter((c) => c.current_status !== "CLOSED");

  function handleChanged(updated: AlertOut) {
    setCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold mb-1">Your outlet</h1>
        <p className="text-sm text-slate-600">
          One shared cash drawer, three separate provider balances. Cash is a derived, read-only figure - not an
          authoritative provider balance, and nothing here merges provider funds.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}). Is aggregator-api running on port 8000?
        </div>
      )}

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

          <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 flex items-center justify-between gap-4 text-sm">
            <span className="text-slate-600">Overall confidence for your outlet</span>
            <ConfidenceBadge level={aggregate.overall_confidence} />
          </div>
        </>
      )}

      <div className="space-y-3">
        <div>
          <h2 className="text-lg font-semibold">Your cases ({openCases.length} open)</h2>
          <p className="text-sm text-slate-600">
            Alerts about your outlet, with a recommended next step. If a case is assigned to you, confirm your
            current cash or balance and add a note - your Field Officer will follow up if needed.
          </p>
        </div>
        {cases.length === 0 && (
          <div className="text-sm text-slate-500 rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center">
            No cases for your outlet right now.
          </div>
        )}
        {cases.map((c) => (
          <AlertCaseCard key={c.id} alert={c} onChanged={handleChanged} />
        ))}
      </div>
    </div>
  );
}

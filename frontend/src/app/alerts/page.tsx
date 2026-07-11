"use client";

import { useEffect, useState } from "react";
import { AgentSelector } from "@/components/AgentSelector";
import { HistoricalOutlierCard, VelocityAnomalyCard } from "@/components/AnomalyCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AGENTS, PROVIDERS, type ProviderId } from "@/lib/agents";
import type { AmountOutlierOut, AnomalyOut } from "@/lib/types";

const POLL_MS = 8000;

export default function AnomalyReviewPage() {
  const { user } = useAuth();
  const isAgentRole = user?.role === "AGENT";
  const [selectedAgent, setSelectedAgent] = useState<string | null>(isAgentRole ? user!.agent_id : AGENTS[0]?.id ?? null);
  const [providerFilter, setProviderFilter] = useState<ProviderId | "">(
    user?.role === "PROVIDER_OPS" ? ((user.provider_id as ProviderId) ?? "") : ""
  );
  const [velocityResults, setVelocityResults] = useState<AnomalyOut[]>([]);
  const [historicalResults, setHistoricalResults] = useState<AmountOutlierOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedAgent) return;
    let cancelled = false;

    async function refresh() {
      try {
        const provider = providerFilter || undefined;
        const [velocity, historical] = await Promise.all([
          api.getAnomalies(selectedAgent!, provider),
          Promise.all(
            (provider ? [provider] : PROVIDERS).map((p) => api.getHistoricalOutliers(selectedAgent!, p))
          ).then((lists) => lists.flat()),
        ]);
        if (!cancelled) {
          setVelocityResults(velocity);
          setHistoricalResults(historical);
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
  }, [selectedAgent, providerFilter]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold mb-1">Anomaly review</h1>
        <p className="text-sm text-slate-600">
          Two independent, explainable checks per provider: a burst-activity detector (frequency + account
          clustering) and a per-agent historical baseline (is this transaction unusual for what this specific agent
          normally does). Both are advisory signals for human review - never a fraud determination, never an
          automated action.
        </p>
      </div>

      <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
        Alert routing, ownership, acknowledgement, escalation, and case resolution are not yet implemented in the
        backend - this page shows the underlying detection evidence directly. The coordination workflow is the next
        phase of this build.
      </div>

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}).
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4">
        {!isAgentRole && <AgentSelector agents={AGENTS} selected={selectedAgent} onSelect={setSelectedAgent} />}
        {user?.role !== "PROVIDER_OPS" && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500">Provider</label>
            <select
              value={providerFilter}
              onChange={(e) => setProviderFilter(e.target.value as ProviderId | "")}
              className="rounded border border-slate-300 bg-white px-2 py-1 text-sm"
            >
              <option value="">All providers</option>
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div className="text-xs uppercase tracking-wide text-slate-500">
          Burst activity ({velocityResults.filter((r) => r.flagged).length} of {velocityResults.length} flagged)
        </div>
        {velocityResults.map((r) => (
          <VelocityAnomalyCard key={`${r.agent_id}-${r.provider}`} result={r} />
        ))}
      </div>

      <div className="space-y-3">
        <div className="text-xs uppercase tracking-wide text-slate-500">
          Unusual for this agent ({historicalResults.filter((r) => r.flagged).length} of {historicalResults.length}{" "}
          flagged)
        </div>
        {historicalResults.map((r) => (
          <HistoricalOutlierCard key={`${r.agent_id}-${r.provider}`} result={r} />
        ))}
      </div>
    </div>
  );
}

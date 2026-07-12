"use client";

import { useEffect, useMemo, useState } from "react";
import { AgentSelector } from "@/components/AgentSelector";
import { AiSummaryPanel } from "@/components/AiSummaryPanel";
import { AlertCaseCard } from "@/components/AlertCaseCard";
import { HistoricalOutlierCard, VelocityAnomalyCard } from "@/components/AnomalyCard";
import { api } from "@/lib/api";
import { summarizeQueue } from "@/lib/aiSummary";
import { useAuth } from "@/lib/auth";
import { AGENTS, PROVIDERS, type ProviderId } from "@/lib/agents";
import type { AlertOut, AmountOutlierOut, AnomalyOut } from "@/lib/types";

const POLL_MS = 8000;
const CASES_PAGE_SIZE = 5;

function isMine(user: { role: string; agent_id: string | null; provider_id: string | null } | null, alert: AlertOut): boolean {
  if (!user) return false;
  if (user.role !== alert.current_owner) return false;
  if (user.role === "AGENT" && alert.agent_id !== user.agent_id) return false;
  if (user.role === "PROVIDER_OPS" && alert.provider !== user.provider_id) return false;
  return true;
}

function CoordinationSection() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showClosed, setShowClosed] = useState(false);
  const [onlyMine, setOnlyMine] = useState(false);
  const [visibleCount, setVisibleCount] = useState(CASES_PAGE_SIZE);

  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const result = await api.getAlerts();
        if (!cancelled) {
          setAlerts(result);
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
  }, []);

  const filtered = useMemo(() => {
    return alerts
      .filter((a) => showClosed || a.current_status !== "CLOSED")
      .filter((a) => !onlyMine || isMine(user, a));
  }, [alerts, showClosed, onlyMine, user]);

  useEffect(() => {
    setVisibleCount(CASES_PAGE_SIZE);
  }, [showClosed, onlyMine]);

  const visible = filtered.slice(0, visibleCount);
  const canSeeMore = visibleCount < filtered.length;
  const canSeeLess = visibleCount > CASES_PAGE_SIZE;

  const openCount = alerts.filter((a) => a.current_status !== "CLOSED").length;
  const mineCount = alerts.filter((a) => a.current_status !== "CLOSED" && isMine(user, a)).length;

  function handleChanged(updated: AlertOut) {
    setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
  }

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-[15px] font-bold">Coordination - assigned cases</h2>
        <p className="text-sm text-slate-600">
          Every liquidity, anomaly, and data-quality alert is automatically assigned to a stakeholder based on
          severity and type, then walks a fixed escalation ladder (Agent → Field Officer → Provider Operations →
          Risk/Compliance → Management) if the current owner can&apos;t resolve it. Nothing here is a fraud
          determination or an automated financial action - every step requires a person to acknowledge, review, and
          decide.
        </p>
      </div>

      <AiSummaryPanel text={summarizeQueue(alerts, "this queue")} />

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}).
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 text-sm">
        <span className="text-slate-600">
          {openCount} open case{openCount === 1 ? "" : "s"} · {mineCount} assigned to you
        </span>
        <label className="flex items-center gap-1.5 text-xs text-slate-600">
          <input type="checkbox" checked={onlyMine} onChange={(e) => setOnlyMine(e.target.checked)} />
          Only assigned to me
        </label>
        <label className="flex items-center gap-1.5 text-xs text-slate-600">
          <input type="checkbox" checked={showClosed} onChange={(e) => setShowClosed(e.target.checked)} />
          Show closed cases
        </label>
      </div>

      <div className="space-y-3">
        {visible.length === 0 && (
          <div className="text-sm text-slate-500 rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center">
            No cases match these filters right now.
          </div>
        )}
        {visible.map((a) => (
          <AlertCaseCard key={a.id} alert={a} onChanged={handleChanged} />
        ))}
      </div>

      {(canSeeMore || canSeeLess) && (
        <div className="flex items-center justify-center gap-3 pt-1">
          {canSeeMore && (
            <button
              onClick={() => setVisibleCount((c) => Math.min(c + CASES_PAGE_SIZE, filtered.length))}
              className="rounded-lg border border-slate-300 bg-white px-4 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
            >
              See more
            </button>
          )}
          {canSeeLess && (
            <button
              onClick={() => setVisibleCount(CASES_PAGE_SIZE)}
              className="rounded-lg border border-slate-300 bg-white px-4 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
            >
              See less
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function EvidenceSection() {
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
    <div className="space-y-3">
      <div>
        <h2 className="text-[15px] font-bold">Detection evidence</h2>
        <p className="text-sm text-slate-600">
          Two independent, explainable checks per provider: a burst-activity detector (frequency + account
          clustering) and a per-agent historical baseline (is this transaction unusual for what this specific agent
          normally does). Flagged results here are what feed the anomaly cases above.
        </p>
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

export default function AnomalyReviewPage() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-[22px] font-extrabold mb-1 tracking-tight">Alerts &amp; coordination</h1>
        <p className="text-[13.5px] text-slate-500 max-w-[600px] leading-relaxed">
          Every alert shows its evidence and confidence, and is routed to a named owner with a recommended next
          step. Advisory signals for human review &mdash; never a fraud determination.
        </p>
      </div>
      <CoordinationSection />
      <EvidenceSection />
    </div>
  );
}

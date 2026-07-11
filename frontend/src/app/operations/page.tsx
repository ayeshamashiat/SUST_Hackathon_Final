"use client";

import { useEffect, useMemo, useState } from "react";
import { AiSummaryPanel } from "@/components/AiSummaryPanel";
import { AlertCaseCard } from "@/components/AlertCaseCard";
import { CaseStatusBadge } from "@/components/Badges";
import { KpiCard } from "@/components/KpiCard";
import { api } from "@/lib/api";
import { summarizeQueue } from "@/lib/aiSummary";
import { useAuth } from "@/lib/auth";
import { average, formatMinutes, isResolvedOrClosed, resolutionRate, timeToResolveMinutes } from "@/lib/caseMetrics";
import { formatRelative } from "@/lib/format";
import { AGENTS, PROVIDER_LABEL, type ProviderId } from "@/lib/agents";
import type { AlertOut, Severity } from "@/lib/types";

const POLL_MS = 8000;
const SEVERITY_RANK: Record<Severity, number> = { HIGH: 2, MEDIUM: 1, LOW: 0 };

function agentName(agentId: string): string {
  return AGENTS.find((a) => a.id === agentId)?.name ?? agentId;
}

export default function OperationsDashboard() {
  const { user } = useAuth();
  const providerLabel = user?.provider_id ? PROVIDER_LABEL[user.provider_id as ProviderId] ?? user.provider_id : "your provider";
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const result = await api.getAlerts(); // backend auto-scopes PROVIDER_OPS to their own provider
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

  const open = alerts.filter((a) => a.current_status !== "CLOSED");
  const mine = open.filter((a) => a.current_owner === "PROVIDER_OPS");
  const resolved = alerts.filter(isResolvedOrClosed);
  const avgResolution = average(resolved.map(timeToResolveMinutes));
  const escalatedByUs = alerts.filter((a) =>
    a.audit_trail.some((e) => e.event_type === "ESCALATED" && e.previous_owner === "PROVIDER_OPS")
  );

  const queue = [...open].sort((a, b) => SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity]);

  const escalationRows = useMemo(
    () =>
      alerts
        .flatMap((a) =>
          a.audit_trail
            .filter((e) => e.event_type === "ESCALATED" && (e.previous_owner === "PROVIDER_OPS" || e.new_owner === "PROVIDER_OPS"))
            .map((e) => ({ alert: a, event: e }))
        )
        .sort((a, b) => new Date(b.event.created_at).getTime() - new Date(a.event.created_at).getTime()),
    [alerts]
  );

  function handleChanged(updated: AlertOut) {
    setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold mb-1">{providerLabel} Operations</h1>
        <p className="text-sm text-slate-600">
          Own liquidity cases for {providerLabel}, coordinate approved operational support, monitor high-priority
          alerts, and assign or reassign cases along the escalation ladder.
        </p>
      </div>

      <AiSummaryPanel text={summarizeQueue(alerts, providerLabel)} />

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}).
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KpiCard label="Open incidents" value={open.length} />
        <KpiCard label="Owned by me" value={mine.length} tone={mine.length > 0 ? "warn" : "default"} />
        <KpiCard label="Escalated by us" value={escalatedByUs.length} />
        <KpiCard label="Resolved (loaded)" value={resolved.length} tone="good" />
        <KpiCard label="Avg. resolution time" value={formatMinutes(avgResolution)} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 flex items-center justify-between gap-4 text-sm">
        <span className="text-slate-600">Resolution rate (loaded cases)</span>
        <span className="font-semibold tabular-nums">
          {resolutionRate(alerts) === null ? "—" : `${resolutionRate(alerts)!.toFixed(0)}%`}
        </span>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Live incident queue ({queue.length})</h2>
        {queue.length === 0 && (
          <div className="text-sm text-slate-500 rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center">
            No open incidents for {providerLabel} right now.
          </div>
        )}
        {queue.map((a) => (
          <AlertCaseCard key={a.id} alert={a} onChanged={handleChanged} />
        ))}
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Escalation activity ({escalationRows.length})</h2>
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="text-left px-4 py-2">When</th>
                <th className="text-left px-4 py-2">Agent</th>
                <th className="text-left px-4 py-2">Direction</th>
                <th className="text-left px-4 py-2">Status</th>
                <th className="text-left px-4 py-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              {escalationRows.map(({ alert, event }) => (
                <tr key={event.id} className="border-t border-slate-100">
                  <td className="px-4 py-2 text-slate-500">{formatRelative(event.created_at)}</td>
                  <td className="px-4 py-2 font-medium text-slate-800">{agentName(alert.agent_id)}</td>
                  <td className="px-4 py-2 text-slate-600">
                    {event.previous_owner === "PROVIDER_OPS" ? `→ ${event.new_owner}` : `${event.previous_owner} →`}
                  </td>
                  <td className="px-4 py-2">
                    <CaseStatusBadge status={alert.current_status} />
                  </td>
                  <td className="px-4 py-2 text-slate-600 truncate max-w-xs">{event.reason ?? "—"}</td>
                </tr>
              ))}
              {escalationRows.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                    No escalations involving Provider Operations yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

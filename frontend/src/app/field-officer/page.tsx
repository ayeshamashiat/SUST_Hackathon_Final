"use client";

import { useEffect, useState } from "react";
import { AiSummaryPanel } from "@/components/AiSummaryPanel";
import { AlertCaseCard } from "@/components/AlertCaseCard";
import { SeverityBadge } from "@/components/Badges";
import { KpiCard } from "@/components/KpiCard";
import { summarizeQueue } from "@/lib/aiSummary";
import { average, formatMinutes, timeToAcknowledgeMinutes } from "@/lib/caseMetrics";
import { api } from "@/lib/api";
import { AGENTS } from "@/lib/agents";
import type { AlertOut, Severity } from "@/lib/types";

const POLL_MS = 8000;
const SEVERITY_RANK: Record<Severity, number> = { HIGH: 2, MEDIUM: 1, LOW: 0 };

function agentName(agentId: string): string {
  return AGENTS.find((a) => a.id === agentId)?.name ?? agentId;
}

export default function FieldOfficerDashboard() {
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [error, setError] = useState<string | null>(null);

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

  const open = alerts.filter((a) => a.current_status !== "CLOSED");
  const mine = open.filter((a) => a.current_owner === "FIELD_OFFICER");
  const highSeverityOpen = open.filter((a) => a.severity === "HIGH");
  const avgAck = average(mine.map(timeToAcknowledgeMinutes));

  const byAgent = new Map<string, AlertOut[]>();
  for (const a of open) {
    if (!byAgent.has(a.agent_id)) byAgent.set(a.agent_id, []);
    byAgent.get(a.agent_id)!.push(a);
  }
  const priorityAgents = Array.from(byAgent.entries())
    .map(([agentId, agentAlerts]) => ({
      agentId,
      count: agentAlerts.length,
      highestSeverity: agentAlerts.reduce<Severity>(
        (max, a) => (SEVERITY_RANK[a.severity] > SEVERITY_RANK[max] ? a.severity : max),
        "LOW"
      ),
      needsMe: agentAlerts.some((a) => a.current_owner === "FIELD_OFFICER"),
    }))
    .sort((a, b) => SEVERITY_RANK[b.highestSeverity] - SEVERITY_RANK[a.highestSeverity] || b.count - a.count);

  const sortedMine = [...mine].sort((a, b) => SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity]);

  function handleChanged(updated: AlertOut) {
    setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold mb-1">Field Officer dashboard</h1>
        <p className="text-sm text-slate-600">
          Verify agent status, contact agents directly, confirm whether a liquidity issue is genuine, and escalate
          to Provider Operations when you can&apos;t resolve it yourself.
        </p>
      </div>

      <AiSummaryPanel text={summarizeQueue(alerts, "the fleet")} />

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}).
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Open cases (fleet)" value={open.length} />
        <KpiCard label="Assigned to me" value={mine.length} tone={mine.length > 0 ? "warn" : "default"} />
        <KpiCard label="High severity open" value={highSeverityOpen.length} tone={highSeverityOpen.length > 0 ? "bad" : "default"} />
        <KpiCard label="Avg. time to acknowledge" value={formatMinutes(avgAck)} sublabel="across your own cases" />
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Assigned agents - priority ranking</h2>
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="text-left px-4 py-2">Agent</th>
                <th className="text-left px-4 py-2">Open cases</th>
                <th className="text-left px-4 py-2">Highest severity</th>
                <th className="text-left px-4 py-2">Needs you</th>
              </tr>
            </thead>
            <tbody>
              {priorityAgents.map((row) => (
                <tr key={row.agentId} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-medium text-slate-800">{agentName(row.agentId)}</td>
                  <td className="px-4 py-2 text-slate-600">{row.count}</td>
                  <td className="px-4 py-2">
                    <SeverityBadge severity={row.highestSeverity} />
                  </td>
                  <td className="px-4 py-2 text-slate-600">{row.needsMe ? "Yes" : "—"}</td>
                </tr>
              ))}
              {priorityAgents.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-slate-500">
                    No open cases right now.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Your verification queue ({sortedMine.length})</h2>
        {sortedMine.length === 0 && (
          <div className="text-sm text-slate-500 rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center">
            Nothing assigned to Field Officer right now.
          </div>
        )}
        {sortedMine.map((a) => (
          <AlertCaseCard key={a.id} alert={a} onChanged={handleChanged} />
        ))}
      </div>
    </div>
  );
}

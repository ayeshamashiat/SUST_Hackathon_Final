"use client";

import { useEffect, useMemo, useState } from "react";
import { AiSummaryPanel } from "@/components/AiSummaryPanel";
import { AlertCaseCard } from "@/components/AlertCaseCard";
import { KpiCard } from "@/components/KpiCard";
import { api } from "@/lib/api";
import { summarizeQueue } from "@/lib/aiSummary";
import { average, formatMinutes, isResolvedOrClosed, resolutionRate, timeToResolveMinutes } from "@/lib/caseMetrics";
import { AGENTS, PROVIDER_LABEL, type ProviderId } from "@/lib/agents";
import type { AlertOut, Severity } from "@/lib/types";

const POLL_MS = 15000;
const SEVERITY_SCORE: Record<Severity, number> = { HIGH: 2, MEDIUM: 1, LOW: 0 };
const AREA_BY_AGENT: Record<string, string> = Object.fromEntries(AGENTS.map((a) => [a.id, a.area]));

function dateKey(iso: string): string {
  return new Date(iso).toLocaleDateString([], { month: "short", day: "numeric" });
}

export default function ManagementDashboard() {
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
  const resolved = alerts.filter(isResolvedOrClosed);
  const avgResolution = average(resolved.map(timeToResolveMinutes));
  const escalated = alerts.filter((a) => a.audit_trail.some((e) => e.event_type === "ESCALATED"));
  const escalationRate = alerts.length ? (escalated.length / alerts.length) * 100 : null;
  const myCases = alerts.filter((a) => a.current_owner === "MANAGEMENT" && a.current_status !== "CLOSED");

  const byArea = new Map<string, AlertOut[]>();
  for (const a of open) {
    const area = AREA_BY_AGENT[a.agent_id] ?? "Unknown";
    if (!byArea.has(area)) byArea.set(area, []);
    byArea.get(area)!.push(a);
  }
  const areaRows = Array.from(byArea.entries())
    .map(([area, list]) => ({
      area,
      openCount: list.length,
      avgSeverity: average(list.map((a) => SEVERITY_SCORE[a.severity])) ?? 0,
    }))
    .sort((a, b) => b.avgSeverity - a.avgSeverity || b.openCount - a.openCount);

  const providerRows = useMemo(() => {
    const providers: ProviderId[] = ["bkash", "nagad", "rocket"];
    return providers.map((p) => {
      const list = alerts.filter((a) => a.provider === p);
      return {
        provider: p,
        openCount: list.filter((a) => a.current_status !== "CLOSED").length,
        resolvedCount: list.filter(isResolvedOrClosed).length,
      };
    });
  }, [alerts]);

  const trendRows = useMemo(() => {
    const byDay = new Map<string, number>();
    for (const a of alerts) {
      const key = dateKey(a.created_at);
      byDay.set(key, (byDay.get(key) ?? 0) + 1);
    }
    return Array.from(byDay.entries());
  }, [alerts]);

  function handleChanged(updated: AlertOut) {
    setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold mb-1">Management overview</h1>
        <p className="text-sm text-slate-600">
          Area-level service risk, provider comparison, and operational readiness across the fleet. Read-only by
          design - individual incidents are owned and worked by Field Officers, Provider Operations, and Risk/
          Compliance, not managed from here.
        </p>
      </div>

      <AiSummaryPanel text={summarizeQueue(alerts, "the fleet")} />

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}).
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KpiCard label="Open (fleet)" value={open.length} />
        <KpiCard label="Resolved (loaded)" value={resolved.length} tone="good" />
        <KpiCard label="Resolution rate" value={resolutionRate(alerts) === null ? "—" : `${resolutionRate(alerts)!.toFixed(0)}%`} />
        <KpiCard label="Avg. resolution time" value={formatMinutes(avgResolution)} />
        <KpiCard
          label="Escalation rate"
          value={escalationRate === null ? "—" : `${escalationRate.toFixed(0)}%`}
          tone={escalationRate !== null && escalationRate > 30 ? "warn" : "default"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Area performance</h2>
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="text-left px-4 py-2">Area</th>
                  <th className="text-left px-4 py-2">Open cases</th>
                  <th className="text-left px-4 py-2">Avg. severity</th>
                </tr>
              </thead>
              <tbody>
                {areaRows.map((row) => (
                  <tr key={row.area} className="border-t border-slate-100">
                    <td className="px-4 py-2 font-medium text-slate-800">{row.area}</td>
                    <td className="px-4 py-2 text-slate-600">{row.openCount}</td>
                    <td className="px-4 py-2 text-slate-600">{row.avgSeverity.toFixed(1)} / 2</td>
                  </tr>
                ))}
                {areaRows.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-6 text-center text-slate-500">
                      No open cases right now.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Provider comparison</h2>
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="text-left px-4 py-2">Provider</th>
                  <th className="text-left px-4 py-2">Open</th>
                  <th className="text-left px-4 py-2">Resolved</th>
                </tr>
              </thead>
              <tbody>
                {providerRows.map((row) => (
                  <tr key={row.provider} className="border-t border-slate-100">
                    <td className="px-4 py-2 font-medium text-slate-800">{PROVIDER_LABEL[row.provider]}</td>
                    <td className="px-4 py-2 text-slate-600">{row.openCount}</td>
                    <td className="px-4 py-2 text-slate-600">{row.resolvedCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Alert volume (loaded window)</h2>
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 flex flex-wrap gap-3 text-sm">
          {trendRows.length === 0 && <span className="text-slate-500">No alerts loaded yet.</span>}
          {trendRows.map(([day, count]) => (
            <div key={day} className="flex flex-col items-center gap-1 min-w-[56px]">
              <div
                className="w-6 bg-slate-700 rounded-t"
                style={{ height: `${Math.max(8, Math.min(60, count * 6))}px` }}
              />
              <span className="text-xs text-slate-500">{day}</span>
              <span className="text-xs font-medium text-slate-700">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {myCases.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Escalated to Management ({myCases.length})</h2>
          <p className="text-sm text-slate-600">
            These cases reached the top of the escalation ladder. Only what&apos;s here needs your direct action.
          </p>
          {myCases.map((a) => (
            <AlertCaseCard key={a.id} alert={a} onChanged={handleChanged} />
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { AlertCard } from "@/components/AlertCard";
import { api } from "@/lib/api";
import type { Agent, AlertOut } from "@/lib/types";

const POLL_MS = 5000;

export default function AlertsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentFilter, setAgentFilter] = useState<string>("");
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    api.listAgents().then(setAgents).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function refresh() {
      try {
        const list = await api.listAlerts({ agentId: agentFilter || undefined, limit: 100 });
        if (!cancelled) {
          setAlerts(list);
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
  }, [agentFilter, refreshKey]);

  const openAlerts = alerts.filter((a) => a.case && a.case.status !== "RESOLVED");
  const resolvedAlerts = alerts.filter((a) => a.case && a.case.status === "RESOLVED");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold mb-1">Alerts &amp; coordination</h1>
        <p className="text-sm text-slate-400">
          Every alert shows its evidence and confidence, and is routed to a named owner with a recommended next
          step. These are advisory signals for human review - not a fraud determination and not an automated
          action.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-2 text-sm text-rose-200">
          Could not reach the backend API ({error}).
        </div>
      )}

      <div className="flex items-center gap-2">
        <label className="text-xs text-slate-500">Filter by agent</label>
        <select
          value={agentFilter}
          onChange={(e) => setAgentFilter(e.target.value)}
          className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm"
        >
          <option value="">All agents</option>
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-3">
        <div className="text-xs uppercase tracking-wide text-slate-500">Open ({openAlerts.length})</div>
        {openAlerts.length === 0 && (
          <p className="text-sm text-slate-500">No open alerts right now - the outlet(s) look healthy.</p>
        )}
        {openAlerts.map((alert) => (
          <AlertCard key={alert.id} alert={alert} onUpdated={() => setRefreshKey((k) => k + 1)} />
        ))}
      </div>

      {resolvedAlerts.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-wide text-slate-500">Resolved ({resolvedAlerts.length})</div>
          {resolvedAlerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} onUpdated={() => setRefreshKey((k) => k + 1)} />
          ))}
        </div>
      )}
    </div>
  );
}

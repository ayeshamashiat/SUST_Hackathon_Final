"use client";

import { useState, useEffect } from "react";
import { AlertCaseCard } from "@/components/AlertCaseCard";
import { KpiCard } from "@/components/KpiCard";
import { api } from "@/lib/api";
import { average } from "@/lib/caseMetrics";
import type { AlertOut } from "@/lib/types";

const POLL_MS = 8000;
const CONFIDENCE_SCORE: Record<string, number> = { HIGH: 100, MEDIUM: 60, LOW: 20 };

export default function RiskDashboard() {
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [includeLiquidity, setIncludeLiquidity] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const result = await api.getAlerts(); // RISK_COMPLIANCE sees the full fleet
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

  const reviewCases = alerts.filter((a) => a.alert_type === "ANOMALY" || a.alert_type === "DATA_QUALITY");
  const visible = includeLiquidity ? alerts.filter((a) => a.current_status !== "CLOSED") : reviewCases.filter((a) => a.current_status !== "CLOSED");
  const mine = alerts.filter((a) => a.current_owner === "RISK_COMPLIANCE" && a.current_status !== "CLOSED");
  const avgConfidence = average(reviewCases.map((a) => CONFIDENCE_SCORE[a.confidence] ?? null));

  function handleChanged(updated: AlertOut) {
    setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold mb-1">Risk &amp; Compliance review</h1>
        <p className="text-sm text-slate-600">
          Review suspicious transaction patterns and data-quality issues, examine the underlying evidence, and
          request further review. Operations teams may escalate a case here, but nothing in this system makes a
          final fraud determination.
        </p>
      </div>

      <div className="rounded-lg border border-indigo-300 bg-indigo-50 px-4 py-2.5 text-sm text-indigo-800">
        Every flagged item below is language-guarded as <strong>&ldquo;requires human review&rdquo;</strong> or
        <strong> &ldquo;unusual activity&rdquo;</strong> - never labeled as confirmed fraud.
      </div>

      {error && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          Could not reach the backend API ({error}).
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Assigned to you" value={mine.length} tone={mine.length > 0 ? "warn" : "default"} />
        <KpiCard label="Anomaly / data-quality cases" value={reviewCases.length} />
        <KpiCard label="Avg. confidence score" value={avgConfidence === null ? "—" : `${avgConfidence.toFixed(0)}%`} />
        <KpiCard label="Open across fleet" value={alerts.filter((a) => a.current_status !== "CLOSED").length} />
      </div>

      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">Review queue ({visible.length})</h2>
        <label className="flex items-center gap-1.5 text-xs text-slate-600">
          <input type="checkbox" checked={includeLiquidity} onChange={(e) => setIncludeLiquidity(e.target.checked)} />
          Also show liquidity cases escalated here
        </label>
      </div>

      {visible.length === 0 && (
        <div className="text-sm text-slate-500 rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center">
          No cases match this filter right now.
        </div>
      )}
      <div className="space-y-3">
        {visible.map((a) => (
          <AlertCaseCard key={a.id} alert={a} onChanged={handleChanged} />
        ))}
      </div>
    </div>
  );
}

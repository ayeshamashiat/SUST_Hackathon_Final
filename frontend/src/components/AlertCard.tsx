"use client";

import { useState } from "react";
import { CaseStatusBadge, ConfidenceBadge, DataQualityBadge, SeverityBadge } from "@/components/Badges";
import { api } from "@/lib/api";
import { ALLOWED_TRANSITIONS, STATUS_LABEL } from "@/lib/caseTransitions";
import { formatRelative } from "@/lib/format";
import type { AlertOut, CaseStatus } from "@/lib/types";

const CATEGORY_LABEL: Record<string, string> = {
  LIQUIDITY: "Liquidity",
  ANOMALY: "Unusual activity - requires review",
  DATA_QUALITY: "Data quality",
};

function formatEvidenceValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  if (Array.isArray(value)) {
    if (value.length === 0) return "-";
    return value
      .map((v) => (typeof v === "object" && v !== null ? JSON.stringify(v) : String(v)))
      .join(", ");
  }
  return String(value);
}

export function AlertCard({ alert, onUpdated }: { alert: AlertOut; onUpdated: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [actor, setActor] = useState("Field Officer (you)");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState<CaseStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const caseData = alert.case;
  const nextStatuses = caseData ? ALLOWED_TRANSITIONS[caseData.status] : [];

  async function handleTransition(status: CaseStatus) {
    if (!caseData) return;
    setSubmitting(status);
    setError(null);
    try {
      await api.updateCase(caseData.id, { status, note: note || undefined, actor });
      setNote("");
      onUpdated();
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden">
      <button
        className="w-full text-left px-4 py-3 flex items-start justify-between gap-4 hover:bg-slate-800/40"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <SeverityBadge severity={alert.severity} />
            <span className="text-xs uppercase tracking-wide text-slate-500">
              {CATEGORY_LABEL[alert.category] ?? alert.category}
            </span>
            {caseData && <CaseStatusBadge status={caseData.status} />}
          </div>
          <div className="font-medium">{alert.title}</div>
          <div className="text-xs text-slate-500">
            {alert.agent_name}
            {alert.provider_name ? ` · ${alert.provider_name}` : ""} &middot; {formatRelative(alert.created_at)}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <ConfidenceBadge level={alert.confidence} />
          <DataQualityBadge quality={alert.data_quality} />
        </div>
      </button>

      {expanded && (
        <div className="border-t border-slate-800 px-4 py-4 space-y-4 text-sm">
          <div className="space-y-2">
            <p className="text-slate-200">{alert.message_en}</p>
            <p className="text-slate-400" lang="bn">
              {alert.message_bn}
            </p>
            <p className="text-xs text-slate-500 italic">{alert.confidence_note}</p>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500 mb-1.5">Evidence</div>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              {Object.entries(alert.evidence).map(([key, value]) => (
                <div key={key} className="contents">
                  <dt className="text-slate-500">{key.replace(/_/g, " ")}</dt>
                  <dd className="text-slate-300 truncate">{formatEvidenceValue(value)}</dd>
                </div>
              ))}
            </dl>
          </div>

          {caseData && (
            <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <div className="text-slate-500">Routed to</div>
                  <div className="text-slate-200">{caseData.stakeholder_role}</div>
                </div>
                <div>
                  <div className="text-slate-500">Owner</div>
                  <div className="text-slate-200">{caseData.owner}</div>
                </div>
                <div className="col-span-2">
                  <div className="text-slate-500">Recommended next step</div>
                  <div className="text-slate-200">{caseData.recommended_action}</div>
                </div>
              </div>

              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">History</div>
                <ul className="space-y-1 text-xs text-slate-400">
                  {caseData.events.map((ev) => (
                    <li key={ev.id}>
                      <span className="text-slate-300">{ev.event_type.replace("_", " ")}</span> by {ev.actor} -{" "}
                      {formatRelative(ev.created_at)}
                      {ev.note ? `: "${ev.note}"` : ""}
                    </li>
                  ))}
                </ul>
              </div>

              {nextStatuses.length > 0 ? (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <div className="flex gap-2">
                    <input
                      value={actor}
                      onChange={(e) => setActor(e.target.value)}
                      placeholder="Your name / role"
                      className="flex-1 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs"
                    />
                  </div>
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Optional note (e.g. what you checked, what you arranged)"
                    className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs"
                    rows={2}
                  />
                  <div className="flex gap-2 flex-wrap">
                    {nextStatuses.map((status) => (
                      <button
                        key={status}
                        disabled={submitting !== null}
                        onClick={() => handleTransition(status)}
                        className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium hover:border-emerald-500/50 hover:text-emerald-300 disabled:opacity-50"
                      >
                        {submitting === status ? "Saving..." : STATUS_LABEL[status]}
                      </button>
                    ))}
                  </div>
                  {error && <p className="text-xs text-rose-400">{error}</p>}
                </div>
              ) : (
                <p className="text-xs text-emerald-400 pt-2 border-t border-slate-800">Case resolved.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

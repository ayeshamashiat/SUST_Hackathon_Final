"use client";

import { Fragment, useState } from "react";
import { CaseStatusBadge, ConfidenceBadge, OwnerBadge, SeverityBadge } from "@/components/Badges";
import { api } from "@/lib/api";
import { formatBDT, formatRelative } from "@/lib/format";
import { PROVIDER_LABEL, type ProviderId } from "@/lib/agents";
import type { AlertOut } from "@/lib/types";
import { useAuth } from "@/lib/auth";

const LANGS = ["en", "bn", "banglish"] as const;
type Lang = (typeof LANGS)[number];
const LANG_LABEL: Record<Lang, string> = { en: "English", bn: "বাংলা", banglish: "Banglish" };

function messageFor(alert: AlertOut, lang: Lang): string {
  if (lang === "bn") return alert.message_bn;
  if (lang === "banglish") return alert.message_banglish;
  return alert.message_en;
}

function providerLabel(provider: string | null): string {
  if (!provider) return "Shared cash";
  return PROVIDER_LABEL[provider as ProviderId] ?? provider;
}

/** Can the logged-in user act on this specific case (mirrors the backend's
 * _can_act in routers/alerts.py - the server is the real authority; this
 * only decides whether to show the action buttons at all). */
function canAct(user: { role: string; agent_id: string | null; provider_id: string | null } | null, alert: AlertOut): boolean {
  if (!user) return false;
  if (user.role !== alert.current_owner) return false;
  if (user.role === "AGENT" && alert.agent_id !== user.agent_id) return false;
  if (user.role === "PROVIDER_OPS" && alert.provider !== user.provider_id) return false;
  return true;
}

export function AlertCaseCard({ alert, onChanged }: { alert: AlertOut; onChanged: (updated: AlertOut) => void }) {
  const { user } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [lang, setLang] = useState<Lang>("en");
  const [note, setNote] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const actable = canAct(user, alert);
  const isClosed = alert.current_status === "CLOSED";

  async function run(action: string, fn: () => Promise<AlertOut>) {
    setBusy(action);
    setError(null);
    try {
      const updated = await fn();
      onChanged(updated);
      setNote("");
      setReason("");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <button
        className="w-full text-left px-4 py-3 flex items-start justify-between gap-4 hover:bg-slate-50"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="space-y-1.5 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <SeverityBadge severity={alert.severity} />
            <CaseStatusBadge status={alert.current_status} />
            <OwnerBadge role={alert.current_owner} />
            <span className="text-xs uppercase tracking-wide text-slate-500">
              {alert.agent_id} · {providerLabel(alert.provider)}
            </span>
          </div>
          <div className="text-sm font-medium text-slate-800 truncate">{alert.title}</div>
          <div className="text-xs text-slate-500">{formatRelative(alert.created_at)}</div>
        </div>
        <ConfidenceBadge level={alert.confidence} />
      </button>

      {expanded && (
        <div className="border-t border-slate-200 px-4 py-4 text-sm space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              {LANGS.map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={`text-xs rounded px-2 py-0.5 border ${
                    lang === l ? "border-emerald-300 bg-emerald-50 text-emerald-800" : "border-slate-200 text-slate-500"
                  }`}
                >
                  {LANG_LABEL[l]}
                </button>
              ))}
            </div>
            <p className="text-slate-800">{messageFor(alert, lang)}</p>
          </div>

          <div className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2">
            <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Recommended next step</div>
            <div className="text-slate-800">{alert.recommended_action}</div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500 mb-1.5">Evidence</div>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              {Object.entries(alert.evidence).map(([k, v]) => (
                <Fragment key={k}>
                  <dt className="text-slate-500">{k.replace(/_/g, " ")}</dt>
                  <dd className="text-slate-700 truncate">
                    {typeof v === "number" && k.toLowerCase().includes("balance") ? formatBDT(v) : String(v ?? "—")}
                  </dd>
                </Fragment>
              ))}
            </dl>
            <div className="text-xs text-slate-500 mt-1.5">{alert.confidence_note}</div>
          </div>

          {actable && !isClosed && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 px-3 py-3 space-y-2">
              <div className="text-xs uppercase tracking-wide text-emerald-800">
                Assigned to you - {alert.current_status.replace(/_/g, " ").toLowerCase()}
              </div>
              <div className="flex flex-wrap gap-2">
                {alert.current_status === "ASSIGNED" && (
                  <button
                    disabled={busy !== null}
                    onClick={() => run("ack", () => api.acknowledgeAlert(alert.id, note || undefined))}
                    className="text-xs rounded bg-indigo-600 text-white px-3 py-1.5 disabled:opacity-50"
                  >
                    Acknowledge
                  </button>
                )}
                {alert.current_status === "ACKNOWLEDGED" && (
                  <button
                    disabled={busy !== null}
                    onClick={() => run("review", () => api.startReview(alert.id, note || undefined))}
                    className="text-xs rounded bg-amber-600 text-white px-3 py-1.5 disabled:opacity-50"
                  >
                    Start review
                  </button>
                )}
                {alert.current_status === "MONITORING" && (
                  <button
                    disabled={busy !== null}
                    onClick={() => run("resume", () => api.startReview(alert.id, note || undefined))}
                    className="text-xs rounded bg-amber-600 text-white px-3 py-1.5 disabled:opacity-50"
                  >
                    Resume review
                  </button>
                )}
                {(alert.current_status === "UNDER_REVIEW" || alert.current_status === "MONITORING") && (
                  <>
                    {alert.current_status === "UNDER_REVIEW" && (
                      <button
                        disabled={busy !== null}
                        onClick={() => run("monitor", () => api.monitorAlert(alert.id, note || undefined))}
                        className="text-xs rounded bg-violet-600 text-white px-3 py-1.5 disabled:opacity-50"
                      >
                        Continue monitoring
                      </button>
                    )}
                    <button
                      disabled={busy !== null}
                      onClick={() => run("resolve", () => api.resolveAlert(alert.id, note || undefined))}
                      className="text-xs rounded bg-emerald-600 text-white px-3 py-1.5 disabled:opacity-50"
                    >
                      Resolve
                    </button>
                    <button
                      disabled={busy !== null || !reason.trim()}
                      onClick={() => run("escalate", () => api.escalateAlert(alert.id, reason))}
                      className="text-xs rounded bg-orange-600 text-white px-3 py-1.5 disabled:opacity-50"
                      title={!reason.trim() ? "Enter an escalation reason first" : undefined}
                    >
                      Escalate
                    </button>
                  </>
                )}
                {alert.current_status === "RESOLVED" && (
                  <button
                    disabled={busy !== null}
                    onClick={() => run("close", () => api.closeAlert(alert.id, note || undefined))}
                    className="text-xs rounded bg-slate-700 text-white px-3 py-1.5 disabled:opacity-50"
                  >
                    Close case
                  </button>
                )}
                <button
                  disabled={busy !== null || !note.trim()}
                  onClick={() => run("note", () => api.addCaseNote(alert.id, note))}
                  className="text-xs rounded border border-slate-300 text-slate-700 px-3 py-1.5 disabled:opacity-50"
                >
                  Add note only
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                <input
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Optional note (shown in the audit trail)"
                  className="flex-1 min-w-[200px] rounded border border-slate-300 px-2 py-1 text-xs"
                />
                <input
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Escalation reason (required to escalate)"
                  className="flex-1 min-w-[200px] rounded border border-slate-300 px-2 py-1 text-xs"
                />
              </div>
              {error && <div className="text-xs text-rose-700">{error}</div>}
            </div>
          )}

          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500 mb-1.5">
              Audit trail ({alert.audit_trail.length})
            </div>
            <ol className="space-y-1 text-xs text-slate-600">
              {alert.audit_trail.map((e) => (
                <li key={e.id} className="flex gap-2">
                  <span className="text-slate-400 tabular-nums">{formatRelative(e.created_at)}</span>
                  <span className="font-medium text-slate-700">{e.event_type.replace(/_/g, " ")}</span>
                  <span className="text-slate-500">by {e.actor}</span>
                  {e.new_owner && (
                    <span className="text-slate-500">
                      → {e.previous_owner ?? "—"} to {e.new_owner}
                    </span>
                  )}
                  {e.note && <span className="text-slate-500 italic">&ldquo;{e.note}&rdquo;</span>}
                  {e.reason && <span className="text-slate-500 italic">reason: {e.reason}</span>}
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}

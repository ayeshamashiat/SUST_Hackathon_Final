import {
  escalationCount,
  formatMinutes,
  timeToAcknowledgeMinutes,
  timeToResolveMinutes,
  timeUnderReviewMinutes,
} from "@/lib/caseMetrics";
import type { AlertOut } from "@/lib/types";

export function ResolutionAnalytics({ alert }: { alert: AlertOut }) {
  if (alert.current_status !== "RESOLVED" && alert.current_status !== "CLOSED") return null;

  const stats = [
    { label: "Time to acknowledge", value: formatMinutes(timeToAcknowledgeMinutes(alert)) },
    { label: "Time under review", value: formatMinutes(timeUnderReviewMinutes(alert)) },
    { label: "Total resolution time", value: formatMinutes(timeToResolveMinutes(alert)) },
    { label: "Escalation count", value: String(escalationCount(alert)) },
  ];

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 px-3.5 py-3">
      <div className="text-xs uppercase tracking-wide text-emerald-800 mb-2">Resolution analytics</div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {stats.map((s) => (
          <div key={s.label}>
            <div className="text-[11px] text-emerald-700/70">{s.label}</div>
            <div className="text-sm font-semibold text-emerald-900">{s.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

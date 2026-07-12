import { formatRelative } from "@/lib/format";
import type { CaseEventOut } from "@/lib/types";

const EVENT_LABEL: Record<string, string> = {
  CREATED: "Alert created",
  ASSIGNED: "Assigned",
  ACKNOWLEDGED: "Acknowledged",
  REVIEW_STARTED: "Review started",
  NOTE_ADDED: "Note added",
  MONITORING: "Continued monitoring",
  ESCALATED: "Escalated",
  REASSIGNED: "Reassigned",
  RESOLVED: "Resolved",
  CLOSED: "Closed",
};

const EVENT_DOT: Record<string, string> = {
  CREATED: "bg-slate-400",
  ASSIGNED: "bg-sky-500",
  ACKNOWLEDGED: "bg-indigo-500",
  REVIEW_STARTED: "bg-amber-500",
  NOTE_ADDED: "bg-slate-400",
  MONITORING: "bg-violet-500",
  ESCALATED: "bg-orange-500",
  REASSIGNED: "bg-orange-500",
  RESOLVED: "bg-emerald-500",
  CLOSED: "bg-slate-500",
};

function absoluteTime(iso: string): string {
  return new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export function CaseTimeline({ events }: { events: CaseEventOut[] }) {
  return (
    <ol className="relative border-l-2 border-[#EFF1F6] pl-4 space-y-3.5">
      {events.map((e) => (
        <li key={e.id} className="relative">
          <span
            className={`absolute -left-[21px] top-0.5 w-2.5 h-2.5 rounded-full ring-2 ring-white ${
              EVENT_DOT[e.event_type] ?? "bg-slate-400"
            }`}
          />
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="text-[13px] font-semibold text-slate-700">{EVENT_LABEL[e.event_type] ?? e.event_type}</span>
            <span className="text-[11px] text-slate-400">
              {absoluteTime(e.created_at)} &middot; {formatRelative(e.created_at)}
            </span>
          </div>
          <div className="text-[12px] text-slate-500">by {e.actor}</div>
          {e.new_owner && (
            <div className="text-[12px] text-slate-500">
              {e.previous_owner ?? "unassigned"} &rarr; {e.new_owner}
            </div>
          )}
          {e.note && <div className="text-[12px] text-slate-600 italic mt-0.5">&ldquo;{e.note}&rdquo;</div>}
          {e.reason && <div className="text-[12px] text-slate-600 italic mt-0.5">Reason: {e.reason}</div>}
        </li>
      ))}
    </ol>
  );
}

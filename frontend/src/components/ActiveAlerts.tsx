import Link from "next/link";
import type { AlertOut, AlertType, Severity } from "@/lib/types";

const CATEGORY_LABEL: Record<AlertType, string> = {
  LIQUIDITY: "Liquidity",
  ANOMALY: "Unusual activity",
  DATA_QUALITY: "Data quality",
};

const SEVERITY_DOT: Record<Severity, string> = {
  HIGH: "bg-rose-500",
  MEDIUM: "bg-amber-500",
  LOW: "bg-slate-400",
};

export function ActiveAlerts({ alerts }: { alerts: AlertOut[] }) {
  const open = alerts.filter((a) => a.current_status !== "CLOSED" && a.current_status !== "RESOLVED");

  return (
    <div className="rounded-2xl border border-[#E8EAF0] bg-white p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <span className="font-bold text-[15px]">Active alerts</span>
        {open.length > 0 && (
          <span className="inline-flex items-center justify-center min-w-[20px] h-5 rounded-full bg-rose-100 text-rose-700 text-[11px] font-bold px-1.5">
            {open.length}
          </span>
        )}
      </div>

      <div className="flex-1 space-y-3">
        {open.length === 0 && <p className="text-[13px] text-slate-400 text-center py-6">No active alerts.</p>}
        {open.slice(0, 4).map((a) => (
          <Link
            key={a.id}
            href="/alerts"
            className="flex items-start gap-2.5 rounded-lg -mx-1 px-1 py-0.5 hover:bg-slate-50"
          >
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${SEVERITY_DOT[a.severity]}`} />
            <div className="min-w-0">
              <div className="text-[13px] font-bold text-slate-800 leading-snug">{a.title}</div>
              <div className="text-[11.5px] text-slate-400">
                {CATEGORY_LABEL[a.alert_type]} &middot; {a.severity.toLowerCase()}
                {a.alert_type === "ANOMALY" ? " · requires review" : ""}
              </div>
            </div>
          </Link>
        ))}
      </div>

      <Link
        href="/alerts"
        className="text-[12.5px] font-semibold text-emerald-600 hover:text-emerald-700 mt-3 self-end"
      >
        View all alerts &amp; cases &rarr;
      </Link>
    </div>
  );
}

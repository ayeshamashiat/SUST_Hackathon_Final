import { ConfidenceBadge, SyncStatusBadge } from "@/components/Badges";
import { formatBDT, formatTime } from "@/lib/format";
import type { ForecastOut, SyncStatus } from "@/lib/types";

function statusStripClass(forecast: ForecastOut | undefined) {
  if (!forecast || forecast.status === "INSUFFICIENT_DATA") return "bg-slate-400";
  if (forecast.status === "STABLE") return "bg-emerald-500";
  if (forecast.minutes_to_shortage !== null && forecast.minutes_to_shortage <= 30) return "bg-rose-500";
  return "bg-amber-500";
}

function monogram(label: string): string {
  const words = label.replace(/\(.*\)/g, "").trim().split(/\s+/);
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return words
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

export function BalanceCard({
  label,
  color,
  balance,
  syncStatus,
  stalenessSeconds,
  forecast,
}: {
  label: string;
  color: string;
  balance: number | null;
  syncStatus?: SyncStatus | null;
  stalenessSeconds?: number | null;
  forecast?: ForecastOut;
}) {
  return (
    <div className="rounded-2xl border border-[#E8EAF0] bg-white overflow-hidden">
      <div className={`h-1 ${statusStripClass(forecast)}`} />
      <div className="p-4 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className="w-[30px] h-[30px] rounded-[9px] flex items-center justify-center font-extrabold text-[11px] shrink-0"
              style={{ backgroundColor: `${color}22`, color }}
            >
              {monogram(label)}
            </div>
            <span className="font-bold text-[13.5px]">{label}</span>
          </div>
          {syncStatus !== undefined && <SyncStatusBadge status={syncStatus} />}
        </div>
        <div className="text-2xl font-extrabold tracking-tight tabular-nums">
          {balance === null ? "—" : formatBDT(balance)}
        </div>
        {stalenessSeconds != null && (
          <div className="text-xs text-slate-500">synced {Math.round(stalenessSeconds)}s ago</div>
        )}

        {forecast && (
          <div className="pt-2.5 border-t border-[#F0F1F6] space-y-1.5">
            <ConfidenceBadge level={forecast.confidence} />
            {forecast.status === "AT_RISK" && forecast.projected_shortage_at ? (
              <p className="text-[12.5px] text-amber-700 leading-snug">
                May run out around <span className="font-semibold">{formatTime(forecast.projected_shortage_at)}</span>
              </p>
            ) : forecast.status === "STABLE" ? (
              <p className="text-[12.5px] text-slate-600 leading-snug">Stable based on recent activity.</p>
            ) : (
              <p className="text-[12.5px] text-slate-500 leading-snug">{forecast.confidence_note}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

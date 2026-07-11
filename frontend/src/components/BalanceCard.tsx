import { ConfidenceBadge, DataQualityBadge, FeedHealthBadge } from "@/components/Badges";
import { formatBDT, formatTime } from "@/lib/format";
import type { FeedHealth, ForecastOut } from "@/lib/types";

function statusStripClass(forecast: ForecastOut | undefined) {
  if (!forecast || forecast.status === "INSUFFICIENT_DATA") return "bg-slate-400";
  if (forecast.status === "STABLE") return "bg-emerald-500";
  if (forecast.minutes_to_shortage !== null && forecast.minutes_to_shortage <= 30) return "bg-rose-500";
  return "bg-amber-500";
}

export function BalanceCard({
  label,
  color,
  balance,
  feedHealth,
  feedUpdatedAt,
  forecast,
}: {
  label: string;
  color: string;
  balance: number;
  feedHealth?: FeedHealth;
  feedUpdatedAt?: string;
  forecast?: ForecastOut;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <div className={`h-1 ${statusStripClass(forecast)}`} />
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
            <span className="font-medium">{label}</span>
          </div>
          {feedHealth && <FeedHealthBadge health={feedHealth} />}
        </div>
        <div className="text-2xl font-semibold tabular-nums">{formatBDT(balance)}</div>
        {feedUpdatedAt && (
          <div className="text-xs text-slate-600">feed updated {formatTime(feedUpdatedAt)}</div>
        )}

        {forecast && (
          <div className="pt-2 border-t border-slate-200 space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <ConfidenceBadge level={forecast.confidence} />
              <DataQualityBadge quality={forecast.data_quality} />
            </div>
            {forecast.status === "AT_RISK" && forecast.projected_shortage_at ? (
              <p className="text-sm text-amber-700">
                May run out around <span className="font-semibold">{formatTime(forecast.projected_shortage_at)}</span>
              </p>
            ) : forecast.status === "STABLE" ? (
              <p className="text-sm text-slate-700">Stable based on recent activity.</p>
            ) : (
              <p className="text-sm text-slate-500">{forecast.confidence_note}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

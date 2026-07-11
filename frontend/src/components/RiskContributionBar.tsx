import type { RiskFactor } from "@/lib/riskContribution";

export function RiskContributionBar({ factors, total }: { factors: RiskFactor[]; total: number }) {
  if (factors.length === 0) return null;
  return (
    <div>
      <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-500 mb-1.5">
        <span>Risk contribution breakdown</span>
        <span className="font-semibold text-slate-700 normal-case tracking-normal">{total}/100</span>
      </div>
      <div className="space-y-1.5">
        {factors.map((f) => (
          <div key={f.label} className="flex items-center gap-2 text-xs">
            <span className="w-52 shrink-0 text-slate-600 truncate" title={f.label}>
              {f.label}
            </span>
            <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full bg-orange-400" style={{ width: `${Math.min(100, (f.points / 60) * 100)}%` }} />
            </div>
            <span className="w-10 text-right font-medium text-slate-700">+{f.points}</span>
          </div>
        ))}
      </div>
      <p className="text-[11px] text-slate-400 mt-1">
        Rule-based weighting for explainability - not a trained model&apos;s feature importance.
      </p>
    </div>
  );
}

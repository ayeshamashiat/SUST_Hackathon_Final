import type { RankedAction } from "@/lib/recommendations";

export function RecommendationList({ actions }: { actions: RankedAction[] }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500 mb-1.5">Recommended actions (ranked)</div>
      <ol className="space-y-1.5">
        {actions.map((a, i) => (
          <li key={a.action} className="flex items-center justify-between gap-3 text-sm">
            <span className="text-slate-800">
              <span className="text-slate-400 mr-1.5">{i + 1}.</span>
              {a.action}
            </span>
            <span className="text-xs font-medium text-slate-500 shrink-0">{a.priority}% priority</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

const TONE_CLASS = {
  default: "text-slate-900",
  good: "text-emerald-700",
  warn: "text-amber-700",
  bad: "text-rose-700",
} as const;

export function KpiCard({
  label,
  value,
  sublabel,
  tone = "default",
}: {
  label: string;
  value: string | number;
  sublabel?: string;
  tone?: keyof typeof TONE_CLASS;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold tabular-nums ${TONE_CLASS[tone]}`}>{value}</div>
      {sublabel && <div className="text-xs text-slate-500 mt-0.5">{sublabel}</div>}
    </div>
  );
}

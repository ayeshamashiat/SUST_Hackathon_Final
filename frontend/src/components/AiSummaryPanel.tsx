export function AiSummaryPanel({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 space-y-1">
      <div className="text-xs font-semibold uppercase tracking-wide text-sky-800">AI Summary</div>
      <p className="text-sm text-sky-900">{text}</p>
      <p className="text-[11px] text-sky-700/70">
        Generated from currently loaded data using fixed templates - not a live model call.
      </p>
    </div>
  );
}

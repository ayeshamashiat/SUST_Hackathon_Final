"use client";

import { useState } from "react";
import { ConfidenceBadge, FlaggedBadge } from "@/components/Badges";
import { formatBDT, formatRelative } from "@/lib/format";
import { PROVIDER_LABEL, type ProviderId } from "@/lib/agents";
import type { AmountOutlierOut, AnomalyOut } from "@/lib/types";

function providerLabel(provider: string): string {
  return PROVIDER_LABEL[provider as ProviderId] ?? provider;
}

/** Velocity + account-clustering check - "is there a burst of activity right now". */
export function VelocityAnomalyCard({ result }: { result: AnomalyOut }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <button
        className="w-full text-left px-4 py-3 flex items-start justify-between gap-4 hover:bg-slate-50"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <FlaggedBadge flagged={result.flagged} />
            <span className="text-xs uppercase tracking-wide text-slate-600">
              {providerLabel(result.provider)} · velocity &amp; clustering
            </span>
          </div>
          <div className="text-sm text-slate-800">{result.message}</div>
        </div>
        <ConfidenceBadge level={result.confidence} />
      </button>

      {expanded && (
        <div className="border-t border-slate-200 px-4 py-4 text-sm">
          <div className="text-xs uppercase tracking-wide text-slate-600 mb-1.5">Evidence</div>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <dt className="text-slate-500">Window count</dt>
            <dd className="text-slate-700">{result.window_count}</dd>
            <dt className="text-slate-500">Baseline mean / stdev</dt>
            <dd className="text-slate-700">
              {result.baseline_mean.toFixed(1)} / {result.baseline_stdev.toFixed(1)}
            </dd>
            <dt className="text-slate-500">z-score</dt>
            <dd className="text-slate-700">{result.z_score !== null ? result.z_score.toFixed(2) : "—"}</dd>
            <dt className="text-slate-500">Unique customers</dt>
            <dd className="text-slate-700">{result.unique_customers}</dd>
            <dt className="text-slate-500">Concentration ratio</dt>
            <dd className="text-slate-700">
              {result.concentration_ratio !== null ? result.concentration_ratio.toFixed(2) : "—"}
            </dd>
            <dt className="text-slate-500">Amount range</dt>
            <dd className="text-slate-700">
              {formatBDT(result.amount_min)} – {formatBDT(result.amount_max)}
            </dd>
            <dt className="text-slate-500">Sample transaction IDs</dt>
            <dd className="text-slate-700 truncate">{result.sample_transaction_ids.join(", ") || "—"}</dd>
            {result.window_end && (
              <>
                <dt className="text-slate-500">Window</dt>
                <dd className="text-slate-700">as of {formatRelative(result.window_end)}</dd>
              </>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}

/** Per-agent historical amount-outlier check - "is this ONE transaction unusual for THIS agent's own history". */
export function HistoricalOutlierCard({ result }: { result: AmountOutlierOut }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <button
        className="w-full text-left px-4 py-3 flex items-start justify-between gap-4 hover:bg-slate-50"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <FlaggedBadge flagged={result.flagged} />
            <span className="text-xs uppercase tracking-wide text-slate-600">
              {providerLabel(result.provider)} · vs. this agent&apos;s own history
            </span>
          </div>
          <div className="text-sm text-slate-800">{result.message}</div>
        </div>
        <ConfidenceBadge level={result.confidence} />
      </button>

      {expanded && (
        <div className="border-t border-slate-200 px-4 py-4 text-sm">
          <div className="text-xs uppercase tracking-wide text-slate-600 mb-1.5">Evidence</div>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <dt className="text-slate-500">Evaluated transaction</dt>
            <dd className="text-slate-700">
              {result.evaluated_transaction_id ?? "—"}
              {result.evaluated_amount !== null ? ` · ${formatBDT(result.evaluated_amount)}` : ""}
            </dd>
            <dt className="text-slate-500">Agent&apos;s historical mean / stdev</dt>
            <dd className="text-slate-700">
              {result.historical_mean !== null ? formatBDT(result.historical_mean) : "—"} /{" "}
              {result.historical_stdev !== null ? formatBDT(result.historical_stdev) : "—"}
            </dd>
            <dt className="text-slate-500">Prior transactions considered</dt>
            <dd className="text-slate-700">{result.historical_sample_size}</dd>
            <dt className="text-slate-500">z-score</dt>
            <dd className="text-slate-700">{result.z_score !== null ? result.z_score.toFixed(2) : "—"}</dd>
            {result.evaluated_at && (
              <>
                <dt className="text-slate-500">Evaluated at</dt>
                <dd className="text-slate-700">{formatRelative(result.evaluated_at)}</dd>
              </>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}

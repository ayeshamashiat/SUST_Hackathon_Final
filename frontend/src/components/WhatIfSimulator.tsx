"use client";

import { useState } from "react";
import { formatBDT, formatTime } from "@/lib/format";
import { recomputeForecast } from "@/lib/whatIf";
import type { ForecastOut } from "@/lib/types";

function targetLabel(f: ForecastOut): string {
  return f.target === "CASH" ? "Shared cash reserve" : f.target_label;
}

function formatMinutes(minutes: number | null): string {
  if (minutes === null) return "no shortage projected";
  if (minutes < 60) return `${Math.round(minutes)} min`;
  return `${(minutes / 60).toFixed(1)} hours`;
}

export function WhatIfSimulator({ forecasts }: { forecasts: ForecastOut[] }) {
  const simulable = forecasts.filter((f) => f.burn_rate_per_minute !== null);
  const [targetKey, setTargetKey] = useState<string>(simulable[0]?.target ?? "");
  const [balanceDelta, setBalanceDelta] = useState(0);
  const [demandPercent, setDemandPercent] = useState(0);

  const forecast = simulable.find((f) => f.target === targetKey) ?? simulable[0];
  const result = forecast
    ? recomputeForecast(forecast, { balanceDelta, demandMultiplierPercent: demandPercent })
    : null;

  if (!forecast) {
    return (
      <div className="rounded-2xl border border-[#E8EAF0] bg-white p-4">
        <span className="font-bold text-[15px]">What-if simulation</span>
        <p className="text-[13px] text-slate-400 mt-2">Not enough recent transaction data yet to simulate.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-[#E8EAF0] bg-white p-4 space-y-4">
      <div className="flex items-center justify-between">
        <span className="font-bold text-[15px]">What-if simulation</span>
        <span className="text-[11px] text-slate-400">Simulated only - never affects real data</span>
      </div>

      {simulable.length > 1 && (
        <select
          value={targetKey}
          onChange={(e) => setTargetKey(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
        >
          {simulable.map((f) => (
            <option key={f.target} value={f.target}>
              {targetLabel(f)}
            </option>
          ))}
        </select>
      )}

      <div className="space-y-3">
        <label className="block">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Additional cash / balance</span>
            <span className="font-semibold text-slate-700">
              {balanceDelta >= 0 ? "+" : ""}
              {formatBDT(balanceDelta)}
            </span>
          </div>
          <input
            type="range"
            min={-20000}
            max={50000}
            step={1000}
            value={balanceDelta}
            onChange={(e) => setBalanceDelta(Number(e.target.value))}
            className="w-full"
          />
        </label>

        <label className="block">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Demand change</span>
            <span className="font-semibold text-slate-700">
              {demandPercent >= 0 ? "+" : ""}
              {demandPercent}%
            </span>
          </div>
          <input
            type="range"
            min={-50}
            max={100}
            step={5}
            value={demandPercent}
            onChange={(e) => setDemandPercent(Number(e.target.value))}
            className="w-full"
          />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-3 pt-1">
        <div className="rounded-xl bg-[#FAFBFD] border border-[#EFF1F6] px-3.5 py-3">
          <div className="text-xs uppercase tracking-wide text-slate-400 mb-1">Current prediction</div>
          <div className="text-slate-800 font-semibold">{formatMinutes(forecast.minutes_to_shortage)}</div>
          {forecast.projected_shortage_at && (
            <div className="text-xs text-slate-400 mt-0.5">around {formatTime(forecast.projected_shortage_at)}</div>
          )}
        </div>
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 px-3.5 py-3">
          <div className="text-xs uppercase tracking-wide text-emerald-700 mb-1">New prediction</div>
          <div className="text-emerald-900 font-semibold">{formatMinutes(result?.minutesToShortage ?? null)}</div>
          {result?.projectedShortageAt && (
            <div className="text-xs text-emerald-700/70 mt-0.5">
              around {formatTime(result.projectedShortageAt.toISOString())}
            </div>
          )}
        </div>
      </div>

      <p className="text-[11px] text-slate-400">
        Recomputed from this outlet&apos;s current burn rate and a mirrored safety threshold - an estimate for
        exploring scenarios, not a guarantee. Does not change any stored balance or transaction.
      </p>
    </div>
  );
}

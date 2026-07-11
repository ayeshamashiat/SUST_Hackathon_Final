"use client";

import { useMemo, useState } from "react";
import { formatBDT } from "@/lib/format";
import type { CashTrendPointOut } from "@/lib/types";

const CHART_W = 560;
const CHART_H = 180;
const PAD = 6;

const CASH_COLOR = "#0E9A85";
const CASH_IN_COLOR = "#2E7FD6";
const CASH_OUT_COLOR = "#E2367B";

function buildPath(values: number[], min: number, span: number) {
  const stepX = (CHART_W - PAD * 2) / Math.max(values.length - 1, 1);
  const points = values.map((v, i) => {
    const x = PAD + i * stepX;
    const y = PAD + (CHART_H - PAD * 2) * (1 - (v - min) / span);
    return [x, y] as const;
  });
  const line = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  return { points, line, stepX };
}

function bucketLabel(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "numeric" });
}

export function CashTrendChart({ points }: { points: CashTrendPointOut[] }) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const chart = useMemo(() => {
    if (points.length === 0) return null;
    const cash = points.map((p) => p.cash_balance);
    const cashIn = points.map((p) => p.cash_in);
    const cashOut = points.map((p) => p.cash_out);
    const all = [...cash, ...cashIn, ...cashOut];
    const max = Math.max(...all);
    const min = Math.min(...all);
    const span = max - min || 1;

    const cashPath = buildPath(cash, min, span);
    const cashInPath = buildPath(cashIn, min, span);
    const cashOutPath = buildPath(cashOut, min, span);
    const areaPath = `${cashPath.line} L${cashPath.points[cashPath.points.length - 1][0].toFixed(1)},${
      CHART_H - PAD
    } L${cashPath.points[0][0].toFixed(1)},${CHART_H - PAD} Z`;

    return { cashPath, cashInPath, cashOutPath, areaPath, stepX: cashPath.stepX };
  }, [points]);

  if (!chart || points.length === 0) {
    return (
      <div className="rounded-2xl border border-[#E8EAF0] bg-white p-4">
        <span className="font-bold text-[15px]">Cash reserve trend</span>
        <p className="text-[13px] text-slate-400 mt-6 mb-6 text-center">Not enough history yet.</p>
      </div>
    );
  }

  const { cashPath, cashInPath, cashOutPath, areaPath, stepX } = chart;
  const hovered = hoverIdx !== null ? points[hoverIdx] : null;

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const relX = ((e.clientX - rect.left) / rect.width) * CHART_W;
    const idx = Math.round((relX - PAD) / stepX);
    setHoverIdx(Math.min(Math.max(idx, 0), points.length - 1));
  }

  const labelStep = Math.max(Math.ceil(points.length / 6), 1);

  return (
    <div className="rounded-2xl border border-[#E8EAF0] bg-white p-4">
      <div className="flex items-center justify-between mb-0.5">
        <span className="font-bold text-[15px]">Cash reserve trend</span>
        <span className="text-[11.5px] text-slate-400">last {points.length}h</span>
      </div>
      <p className="text-xs text-slate-400 mb-1.5">Shared cash drawer balance, sampled hourly</p>

      <div className="relative">
        <svg
          viewBox={`0 0 ${CHART_W} ${CHART_H}`}
          className="w-full h-[150px] block cursor-crosshair"
          preserveAspectRatio="none"
          onMouseMove={handleMove}
          onMouseLeave={() => setHoverIdx(null)}
        >
          <defs>
            <linearGradient id="cashTrendGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CASH_COLOR} stopOpacity="0.35" />
              <stop offset="100%" stopColor={CASH_COLOR} stopOpacity="0.03" />
            </linearGradient>
          </defs>
          <path d={areaPath} fill="url(#cashTrendGrad)" stroke="none" />
          <path d={cashOutPath.line} fill="none" stroke={CASH_OUT_COLOR} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="5 4" />
          <path d={cashInPath.line} fill="none" stroke={CASH_IN_COLOR} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="5 4" />
          <path d={cashPath.line} fill="none" stroke={CASH_COLOR} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

          {hoverIdx !== null && (
            <>
              <line
                x1={cashPath.points[hoverIdx][0]}
                x2={cashPath.points[hoverIdx][0]}
                y1={PAD}
                y2={CHART_H - PAD}
                stroke="#D8DCE6"
                strokeWidth="1"
              />
              <circle cx={cashPath.points[hoverIdx][0]} cy={cashPath.points[hoverIdx][1]} r="3.5" fill={CASH_COLOR} stroke="#FFFFFF" strokeWidth="1.5" />
              <circle cx={cashInPath.points[hoverIdx][0]} cy={cashInPath.points[hoverIdx][1]} r="3" fill={CASH_IN_COLOR} stroke="#FFFFFF" strokeWidth="1.5" />
              <circle cx={cashOutPath.points[hoverIdx][0]} cy={cashOutPath.points[hoverIdx][1]} r="3" fill={CASH_OUT_COLOR} stroke="#FFFFFF" strokeWidth="1.5" />
            </>
          )}
        </svg>

        {hovered && hoverIdx !== null && (
          <div
            className="absolute top-1 rounded-lg border border-[#E8EAF0] bg-white px-2.5 py-2 shadow-md text-[11px] pointer-events-none space-y-1 min-w-[128px]"
            style={{
              left: `${Math.min(Math.max((cashPath.points[hoverIdx][0] / CHART_W) * 100, 12), 88)}%`,
              transform: "translateX(-50%)",
            }}
          >
            <div className="font-semibold text-slate-700">{bucketLabel(hovered.bucket_end)}</div>
            <div className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-1.5 text-slate-500"><span className="w-2 h-2 rounded-full" style={{ background: CASH_COLOR }} />Reserve</span>
              <span className="font-semibold tabular-nums">{formatBDT(hovered.cash_balance)}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-1.5 text-slate-500"><span className="w-2 h-2 rounded-full" style={{ background: CASH_IN_COLOR }} />Cash-in</span>
              <span className="font-semibold tabular-nums">{formatBDT(hovered.cash_in)}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-1.5 text-slate-500"><span className="w-2 h-2 rounded-full" style={{ background: CASH_OUT_COLOR }} />Cash-out</span>
              <span className="font-semibold tabular-nums">{formatBDT(hovered.cash_out)}</span>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-between text-[10.5px] text-slate-300 mt-0.5">
        {points.map((p, i) =>
          i % labelStep === 0 || i === points.length - 1 ? <span key={p.bucket_end}>{bucketLabel(p.bucket_end)}</span> : <span key={p.bucket_end} />
        )}
      </div>

      <div className="flex gap-4 mt-2.5">
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2.5 h-[2.5px] rounded-sm inline-block" style={{ background: CASH_COLOR }} />
          Cash reserve
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2.5 h-[2.5px] rounded-sm inline-block" style={{ background: CASH_IN_COLOR }} />
          Cash-in
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2.5 h-[2.5px] rounded-sm inline-block" style={{ background: CASH_OUT_COLOR }} />
          Cash-out
        </span>
      </div>
    </div>
  );
}

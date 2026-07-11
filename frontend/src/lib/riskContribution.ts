// Explainable, rule-based decomposition of "why was this flagged" into
// named contributing factors with illustrative point weights - the same
// philosophy as the backend's detectors (services/anomaly.py, forecast.py):
// no black-box model, so no fabricated feature-importance values either.
// These weights are hand-authored for explainability, not fitted to data -
// documented here rather than silently presented as calibrated statistics.
import type { AlertOut } from "./types";

export interface RiskFactor {
  label: string;
  points: number;
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function clamp(n: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, n));
}

export function riskContribution(alert: AlertOut): { factors: RiskFactor[]; total: number } {
  const e = alert.evidence;
  const factors: RiskFactor[] = [];

  switch (alert.metric) {
    case "velocity_spike": {
      const z = num(e.z_score);
      const concentration = num(e.concentration_ratio);
      const count = num(e.window_count);
      const min = num(e.amount_min);
      const max = num(e.amount_max);
      if (z !== null) factors.push({ label: "Rapid cash-out activity vs. baseline", points: clamp(Math.round(z * 10), 0, 40) });
      if (concentration !== null)
        factors.push({ label: "Concentrated in a small group of accounts", points: clamp(Math.round((1 - concentration) * 30), 0, 30) });
      if (count !== null) factors.push({ label: "High transaction count in a short window", points: clamp(Math.round(count * 1.5), 0, 15) });
      if (min !== null && max !== null && max > 0 && (max - min) / max < 0.05) {
        factors.push({ label: "Near-identical transaction amounts", points: 10 });
      }
      break;
    }
    case "amount_outlier": {
      const z = num(e.z_score);
      const sample = num(e.historical_sample_size);
      if (z !== null)
        factors.push({ label: "Deviation from this agent's own historical average", points: clamp(Math.round(z * 12), 0, 55) });
      if (sample !== null)
        factors.push({ label: `Historical sample depth (${sample} prior transactions)`, points: sample < 30 ? 5 : 15 });
      break;
    }
    case "cash_burn_rate":
    case "provider_burn_rate": {
      const minutes = num(e.minutes_to_shortage);
      const burn = num(e.burn_rate_per_minute);
      if (minutes !== null) factors.push({ label: "Time pressure until projected shortage", points: clamp(Math.round(60 - minutes / 3), 0, 55) });
      if (burn !== null) factors.push({ label: "Sustained cash burn rate", points: clamp(Math.round(Math.abs(burn) / 40), 0, 25) });
      const contributors = e.top_contributors as { provider: string; share: number }[] | undefined;
      if (Array.isArray(contributors) && contributors[0]) {
        factors.push({
          label: `Concentrated in ${contributors[0].provider}`,
          points: clamp(Math.round(contributors[0].share * 20), 0, 20),
        });
      }
      break;
    }
    case "feed_sync_status": {
      const stale = num(e.staleness_seconds);
      const status = e.sync_status as string | undefined;
      if (stale !== null) factors.push({ label: "Provider feed delay", points: clamp(Math.round(stale / 8), 0, 55) });
      if (status) factors.push({ label: `Feed status: ${status}`, points: status === "ok" ? 0 : status === "delayed" ? 15 : 30 });
      break;
    }
  }

  const total = clamp(
    factors.reduce((sum, f) => sum + f.points, 0),
    0,
    100
  );
  return { factors, total };
}

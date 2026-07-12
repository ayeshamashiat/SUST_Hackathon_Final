// Client-side "what if" recomputation - never sends anything to the
// backend and never touches real data, per the brief's requirement that
// simulation "should update predictions dynamically without affecting
// actual data." Reuses the exact forecast a dashboard already fetched;
// only the safety threshold has to be mirrored here as a constant (see
// backend/aggregator-api/app/config.py's CASH_SAFETY_THRESHOLD /
// PROVIDER_SAFETY_THRESHOLD - both 5,000 BDT today) since the API doesn't
// expose it. If that constant changes on the backend, update it here too.
import type { ForecastOut } from "./types";

export const WHATIF_SAFETY_THRESHOLD = 5_000;

export interface WhatIfResult {
  newBalance: number;
  newRatePerMinute: number | null;
  minutesToShortage: number | null;
  projectedShortageAt: Date | null;
}

export function recomputeForecast(
  forecast: ForecastOut,
  adjustments: { balanceDelta: number; demandMultiplierPercent: number }
): WhatIfResult {
  const newBalance = forecast.current_balance + adjustments.balanceDelta;
  const demandMultiplier = 1 + adjustments.demandMultiplierPercent / 100;

  if (forecast.burn_rate_per_minute === null) {
    return { newBalance, newRatePerMinute: null, minutesToShortage: null, projectedShortageAt: null };
  }

  const newRate = forecast.burn_rate_per_minute * demandMultiplier;

  if (newRate >= 0) {
    return { newBalance, newRatePerMinute: newRate, minutesToShortage: null, projectedShortageAt: null };
  }

  const minutes = Math.max((newBalance - WHATIF_SAFETY_THRESHOLD) / Math.abs(newRate), 0);
  const projectedAt = new Date(Date.now() + minutes * 60_000);
  return { newBalance, newRatePerMinute: newRate, minutesToShortage: minutes, projectedShortageAt: projectedAt };
}

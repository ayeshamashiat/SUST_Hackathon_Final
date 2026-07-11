// Resolution-analytics helpers - all derived client-side from AlertOut's
// already-fetched audit_trail (see cases/models.py's CaseEvent docstring on
// the backend). No dedicated backend endpoint yet: Phase 1 only needs
// numbers that are already fully present in the data each dashboard fetches.
import type { AlertOut } from "./types";

function minutesBetween(a: string, b: string): number {
  return (new Date(b).getTime() - new Date(a).getTime()) / 60000;
}

export function timeToAcknowledgeMinutes(alert: AlertOut): number | null {
  const ack = alert.audit_trail.find((e) => e.event_type === "ACKNOWLEDGED");
  return ack ? minutesBetween(alert.created_at, ack.created_at) : null;
}

export function timeToResolveMinutes(alert: AlertOut): number | null {
  const done = alert.audit_trail.find((e) => e.event_type === "RESOLVED" || e.event_type === "CLOSED");
  return done ? minutesBetween(alert.created_at, done.created_at) : null;
}

export function escalationCount(alert: AlertOut): number {
  return alert.audit_trail.filter((e) => e.event_type === "ESCALATED").length;
}

export function isOpen(alert: AlertOut): boolean {
  return alert.current_status !== "CLOSED";
}

export function isResolvedOrClosed(alert: AlertOut): boolean {
  return alert.current_status === "RESOLVED" || alert.current_status === "CLOSED";
}

export function average(nums: (number | null)[]): number | null {
  const valid = nums.filter((n): n is number => n !== null && Number.isFinite(n));
  if (!valid.length) return null;
  return valid.reduce((a, b) => a + b, 0) / valid.length;
}

export function formatMinutes(minutes: number | null): string {
  if (minutes === null) return "—";
  if (minutes < 60) return `${Math.round(minutes)}m`;
  return `${(minutes / 60).toFixed(1)}h`;
}

export function resolutionRate(alerts: AlertOut[]): number | null {
  if (!alerts.length) return null;
  const resolved = alerts.filter(isResolvedOrClosed).length;
  return (resolved / alerts.length) * 100;
}

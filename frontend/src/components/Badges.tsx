import type { CaseStatus, ConfidenceLevel, DataQuality, FeedHealth } from "@/lib/types";

function badge(className: string, label: string, key?: string) {
  return (
    <span
      key={key}
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${className}`}
    >
      {label}
    </span>
  );
}

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const styles: Record<ConfidenceLevel, string> = {
    HIGH: "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
    MEDIUM: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
    LOW: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
  };
  return badge(styles[level], `${level} confidence`);
}

export function SeverityBadge({ severity }: { severity: "LOW" | "MEDIUM" | "HIGH" }) {
  const styles = {
    HIGH: "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
    MEDIUM: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
    LOW: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
  };
  return badge(styles[severity], severity);
}

export function CaseStatusBadge({ status }: { status: CaseStatus }) {
  const styles: Record<CaseStatus, string> = {
    NEW: "bg-sky-100 text-sky-800 ring-1 ring-sky-200",
    ACKNOWLEDGED: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
    IN_PROGRESS: "bg-violet-100 text-violet-800 ring-1 ring-violet-200",
    ESCALATED: "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
    RESOLVED: "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
  };
  return badge(styles[status], status.replace("_", " "));
}

export function DataQualityBadge({ quality }: { quality: DataQuality }) {
  if (quality === "OK") return null;
  return badge("bg-rose-100 text-rose-800 ring-1 ring-rose-200", "Degraded data - low confidence");
}

export function FeedHealthBadge({ health }: { health: FeedHealth }) {
  if (health === "OK") return badge("bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200", "Feed OK");
  return badge("bg-rose-100 text-rose-800 ring-1 ring-rose-200", "Feed delayed");
}

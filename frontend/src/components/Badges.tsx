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
    HIGH: "bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30",
    MEDIUM: "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30",
    LOW: "bg-slate-500/15 text-slate-300 ring-1 ring-slate-500/30",
  };
  return badge(styles[level], `${level} confidence`);
}

export function SeverityBadge({ severity }: { severity: "LOW" | "MEDIUM" | "HIGH" }) {
  const styles = {
    HIGH: "bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/30",
    MEDIUM: "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30",
    LOW: "bg-slate-500/15 text-slate-300 ring-1 ring-slate-500/30",
  };
  return badge(styles[severity], severity);
}

export function CaseStatusBadge({ status }: { status: CaseStatus }) {
  const styles: Record<CaseStatus, string> = {
    NEW: "bg-sky-500/15 text-sky-300 ring-1 ring-sky-500/30",
    ACKNOWLEDGED: "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30",
    IN_PROGRESS: "bg-violet-500/15 text-violet-300 ring-1 ring-violet-500/30",
    ESCALATED: "bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/30",
    RESOLVED: "bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30",
  };
  return badge(styles[status], status.replace("_", " "));
}

export function DataQualityBadge({ quality }: { quality: DataQuality }) {
  if (quality === "OK") return null;
  return badge("bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/30", "Degraded data - low confidence");
}

export function FeedHealthBadge({ health }: { health: FeedHealth }) {
  if (health === "OK") return badge("bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30", "Feed OK");
  return badge("bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/30", "Feed delayed");
}

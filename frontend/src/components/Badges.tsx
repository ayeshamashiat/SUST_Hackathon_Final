import type { CaseStatus, ConfidenceLevel, Severity, SyncStatus, UserRole } from "@/lib/types";

function badge(className: string, label: string) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${className}`}>
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

export function SyncStatusBadge({ status }: { status: SyncStatus | null | undefined }) {
  if (!status) return badge("bg-slate-100 text-slate-600 ring-1 ring-slate-200", "Never synced");
  const styles: Record<SyncStatus, string> = {
    ok: "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
    delayed: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
    failed: "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
    conflicting: "bg-violet-100 text-violet-800 ring-1 ring-violet-200",
  };
  const label: Record<SyncStatus, string> = {
    ok: "Synced",
    delayed: "Feed delayed",
    failed: "Sync failed",
    conflicting: "Data conflicting",
  };
  return badge(styles[status], label[status]);
}

export function FlaggedBadge({ flagged }: { flagged: boolean }) {
  return flagged
    ? badge("bg-rose-100 text-rose-800 ring-1 ring-rose-200", "Requires review")
    : badge("bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200", "Normal pattern");
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const styles: Record<Severity, string> = {
    HIGH: "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
    MEDIUM: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
    LOW: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
  };
  return badge(styles[severity], `${severity} severity`);
}

export function CaseStatusBadge({ status }: { status: CaseStatus }) {
  const styles: Record<CaseStatus, string> = {
    NEW: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
    ASSIGNED: "bg-sky-100 text-sky-800 ring-1 ring-sky-200",
    ACKNOWLEDGED: "bg-indigo-100 text-indigo-800 ring-1 ring-indigo-200",
    UNDER_REVIEW: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
    MONITORING: "bg-violet-100 text-violet-800 ring-1 ring-violet-200",
    ESCALATED: "bg-orange-100 text-orange-800 ring-1 ring-orange-200",
    RESOLVED: "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
    CLOSED: "bg-slate-200 text-slate-600 ring-1 ring-slate-300",
  };
  const label = status.replace(/_/g, " ");
  return badge(styles[status], label);
}

export const ROLE_LABEL: Record<UserRole, string> = {
  AGENT: "Agent",
  FIELD_OFFICER: "Field Officer",
  AREA_MANAGER: "Area Manager",
  PROVIDER_OPS: "Provider Operations",
  RISK_COMPLIANCE: "Risk / Compliance",
  MANAGEMENT: "Management",
};

export function OwnerBadge({ role }: { role: UserRole }) {
  return badge("bg-white text-slate-700 ring-1 ring-slate-300", ROLE_LABEL[role]);
}

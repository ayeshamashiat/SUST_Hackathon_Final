import type { CaseStatus } from "./types";

export const ALLOWED_TRANSITIONS: Record<CaseStatus, CaseStatus[]> = {
  NEW: ["ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED"],
  ACKNOWLEDGED: ["IN_PROGRESS", "ESCALATED", "RESOLVED"],
  IN_PROGRESS: ["ESCALATED", "RESOLVED"],
  ESCALATED: ["RESOLVED"],
  RESOLVED: [],
};

export const STATUS_LABEL: Record<CaseStatus, string> = {
  NEW: "Acknowledge",
  ACKNOWLEDGED: "Acknowledge",
  IN_PROGRESS: "Start work",
  ESCALATED: "Escalate",
  RESOLVED: "Resolve",
};

// Page-level "AI Summary" panel text - a fixed template filled in from
// whatever alerts the page already fetched. Deliberately NOT a live LLM
// call (Phase 8/services/llm.py on the backend isn't built yet, and this
// project's standing rule is mock-mode-by-default with no live model call
// without an explicit go-ahead) - the caller should always pair this with a
// visible "not a live model call" caption so nobody mistakes fixed
// templating for a real generative summary.
import { PROVIDER_LABEL, type ProviderId } from "./agents";
import type { AlertOut, AlertType, Severity } from "./types";

const SEVERITY_RANK: Record<Severity, number> = { HIGH: 2, MEDIUM: 1, LOW: 0 };

const TYPE_LABEL: Record<AlertType, string> = {
  LIQUIDITY: "liquidity pressure",
  ANOMALY: "unusual transaction activity",
  DATA_QUALITY: "data-quality issues",
};

export function summarizeQueue(alerts: AlertOut[], scopeLabel: string): string {
  const open = alerts.filter((a) => a.current_status !== "CLOSED");
  if (open.length === 0) {
    return `No open cases for ${scopeLabel} in the currently loaded data - nothing needs attention right now.`;
  }

  const high = open.filter((a) => a.severity === "HIGH");

  const byType = new Map<AlertType, number>();
  for (const a of open) byType.set(a.alert_type, (byType.get(a.alert_type) ?? 0) + 1);
  const dominantType = [...byType.entries()].sort((a, b) => b[1] - a[1])[0];

  const byProvider = new Map<string, number>();
  for (const a of open) if (a.provider) byProvider.set(a.provider, (byProvider.get(a.provider) ?? 0) + 1);
  const dominantProvider = [...byProvider.entries()].sort((a, b) => b[1] - a[1])[0];

  const mostUrgent = [...open].sort((a, b) => SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity])[0];

  const sentences: string[] = [];
  sentences.push(
    `${open.length} open case${open.length === 1 ? "" : "s"} for ${scopeLabel}` +
      (high.length ? `, ${high.length} at high severity.` : ".")
  );
  if (dominantType) {
    const providerPart = dominantProvider
      ? `, primarily from ${PROVIDER_LABEL[dominantProvider[0] as ProviderId] ?? dominantProvider[0]}`
      : "";
    sentences.push(`Most cases involve ${TYPE_LABEL[dominantType[0]]}${providerPart}.`);
  }
  if (mostUrgent) {
    sentences.push(`Most urgent: "${mostUrgent.title}". Recommended: ${mostUrgent.recommended_action}`);
  }
  return sentences.join(" ");
}

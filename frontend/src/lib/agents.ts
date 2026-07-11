// Static mirror of backend/provider-api/app/seed_data.py's AGENTS list.
// No endpoint currently exposes an agent list from aggregator-api - only
// /aggregate/agent/{agent_id} exists, which requires already knowing an
// agent_id. Hardcoded here rather than adding new backend surface for it.
// If provider-api's seed data ever changes, update this to match.
import type { Agent } from "./types";

export const AGENTS: Agent[] = [
  { id: "agent-001", name: "Zindabazar Bazar Corner", area: "Zindabazar" },
  { id: "agent-002", name: "Shahjalal Uposhohor Outlet", area: "Uposhohor" },
  { id: "agent-003", name: "Amberkhana Point", area: "Amberkhana" },
  { id: "agent-004", name: "Bandar Bazar Trading", area: "Bandar Bazar" },
  { id: "agent-005", name: "Kumarpara Mobile Banking", area: "Kumarpara" },
  { id: "agent-006", name: "Mirabazar Service Center", area: "Mirabazar" },
  { id: "agent-007", name: "Chowhatta Corner Shop", area: "Chowhatta" },
  { id: "agent-008", name: "Tilagor Junction Outlet", area: "Tilagor" },
  { id: "agent-009", name: "Shibganj Bazar Stall", area: "Shibganj" },
  { id: "agent-010", name: "Modina Market Booth", area: "Modina Market" },
  { id: "agent-011", name: "Court Point Agent Shop", area: "Court Point" },
  { id: "agent-012", name: "Subid Bazar Outlet", area: "Subid Bazar" },
  { id: "agent-013", name: "Rikabibazar Service Point", area: "Rikabibazar" },
  { id: "agent-014", name: "Lamabazar Corner Store", area: "Lamabazar" },
  { id: "agent-015", name: "Naiorpul Mobile Point", area: "Naiorpul" },
];

export const PROVIDERS = ["bkash", "nagad", "rocket"] as const;
export type ProviderId = (typeof PROVIDERS)[number];

export const PROVIDER_LABEL: Record<ProviderId, string> = {
  bkash: "bKash",
  nagad: "Nagad",
  rocket: "Rocket",
};

// Real bKash/Nagad/Rocket brand colors - matches provider-api/app/seed_data.py-era
// conventions from the earlier prototype, kept for visual continuity.
export const PROVIDER_COLOR: Record<ProviderId, string> = {
  bkash: "#E2136E",
  nagad: "#C97300",
  rocket: "#6C2EB9",
};

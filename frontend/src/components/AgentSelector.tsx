"use client";

import type { Agent } from "@/lib/types";

export function AgentSelector({
  agents,
  selected,
  onSelect,
}: {
  agents: Agent[];
  selected: string | null;
  onSelect: (agentId: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {agents.map((agent) => (
        <button
          key={agent.id}
          onClick={() => onSelect(agent.id)}
          className={`rounded-lg px-3 py-2 text-sm text-left transition-colors border ${
            selected === agent.id
              ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-200"
              : "border-slate-800 bg-slate-900 text-slate-300 hover:border-slate-700"
          }`}
        >
          <div className="font-medium">{agent.name}</div>
          <div className="text-xs text-slate-500">{agent.area}</div>
        </button>
      ))}
    </div>
  );
}

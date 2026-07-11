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
              ? "border-emerald-300 bg-emerald-50 text-emerald-800"
              : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
          }`}
        >
          <div className="font-medium">{agent.name}</div>
          <div className="text-xs text-slate-500">{agent.area}</div>
        </button>
      ))}
    </div>
  );
}

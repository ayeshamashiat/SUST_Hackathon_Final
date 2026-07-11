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
          className={`rounded-xl px-3 py-2 text-sm text-left transition-colors border ${
            selected === agent.id
              ? "border-accent-light bg-accent-light/40 text-accent"
              : "border-[#E3E6EE] bg-white text-slate-700 hover:border-slate-300"
          }`}
        >
          <div className="font-semibold text-[13px]">{agent.name}</div>
          <div className="text-[11px] text-slate-400">{agent.area}</div>
        </button>
      ))}
    </div>
  );
}

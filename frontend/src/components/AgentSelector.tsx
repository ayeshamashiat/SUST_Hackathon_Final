"use client";

import { useEffect, useRef, useState } from "react";
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
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const current = agents.find((a) => a.id === selected) ?? agents[0];

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={rootRef} className="relative w-64">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 rounded-xl border border-[#E3E6EE] bg-white pl-4 pr-3 py-2.5 text-left hover:border-slate-300 focus:outline-none focus:border-accent-light"
      >
        <div className="min-w-0">
          <div className="font-semibold text-[13px] text-slate-700 truncate">{current?.name}</div>
          <div className="text-[11px] text-slate-400 truncate">{current?.area}</div>
        </div>
        <svg
          className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
        >
          <path d="M6 8l4 4 4-4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 z-10 mt-1 w-full rounded-xl border border-[#E3E6EE] bg-white py-1 shadow-lg">
          {agents.map((agent) => (
            <button
              key={agent.id}
              type="button"
              onClick={() => {
                onSelect(agent.id);
                setOpen(false);
              }}
              className={`block w-full px-4 py-2 text-left transition-colors ${
                selected === agent.id ? "bg-accent-light/40" : "hover:bg-slate-50"
              }`}
            >
              <div className={`font-semibold text-[13px] ${selected === agent.id ? "text-accent" : "text-slate-700"}`}>
                {agent.name}
              </div>
              <div className="text-[11px] text-slate-400">{agent.area}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

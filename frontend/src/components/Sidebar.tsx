"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ROLE_LABEL } from "@/components/Badges";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/alerts", label: "Alerts & Cases" },
] as const;

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return parts
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="w-[248px] shrink-0 bg-white border-r border-slate-200 flex flex-col p-4">
      <div className="flex items-center gap-2.5 px-2 mb-7">
        <div className="w-9 h-9 rounded-[10px] bg-accent-ink flex items-center justify-center shrink-0">
          <div className="w-[15px] h-[15px] rounded-[4px] bg-accent-light" />
        </div>
        <div>
          <div className="font-extrabold text-[13.5px] leading-tight text-slate-900">SUPER AGENT</div>
          <div className="font-semibold text-[10px] tracking-[0.12em] text-slate-400">CONSOLE</div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-semibold transition-colors ${
                active ? "bg-accent-light text-accent" : "text-slate-500 hover:bg-slate-50"
              }`}
            >
              <span className={`w-2 h-2 rounded-[3px] ${active ? "bg-accent" : "bg-slate-400"}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {user && (
        <div className="mt-auto pt-4 border-t border-slate-100">
          <div className="flex items-center gap-2.5 px-2 pb-3">
            <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-xs shrink-0">
              {initials(user.display_name)}
            </div>
            <div className="min-w-0">
              <div className="text-[13px] font-semibold text-slate-900 truncate">{user.display_name}</div>
              <div className="text-[11px] text-slate-400">{ROLE_LABEL[user.role] ?? user.role}</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full border border-slate-200 bg-white rounded-[10px] py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
          >
            Log out
          </button>
        </div>
      )}
    </div>
  );
}

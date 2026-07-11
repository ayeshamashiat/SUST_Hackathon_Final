"use client";

import { ROLE_LABEL } from "@/components/Badges";
import { useAuth } from "@/lib/auth";

export function UserBadge() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-slate-600 hidden sm:inline">
        {user.display_name} <span className="text-slate-400">- {ROLE_LABEL[user.role] ?? user.role}</span>
      </span>
      <button
        onClick={logout}
        className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50 transition-colors"
      >
        Log out
      </button>
    </div>
  );
}

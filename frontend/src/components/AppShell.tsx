"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { AuthGate } from "@/components/AuthGate";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (pathname === "/login") {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <AuthGate>{children}</AuthGate>
      </div>
    );
  }

  return (
    <div className="flex flex-1 min-h-screen">
      <Sidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <main className="flex-1 min-w-0 px-8 py-7">
          <AuthGate>{children}</AuthGate>
        </main>
        <footer className="px-8 py-3 text-center text-[11.5px] text-slate-400">
          Simulated data only &middot; advisory alerts, never an automated financial action &middot; human review
          required
        </footer>
      </div>
    </div>
  );
}

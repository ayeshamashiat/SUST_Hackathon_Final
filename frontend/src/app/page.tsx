"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import type { UserRole } from "@/lib/types";

const ROLE_HOME: Record<UserRole, string> = {
  AGENT: "/agent",
  FIELD_OFFICER: "/field-officer",
  AREA_MANAGER: "/management",
  PROVIDER_OPS: "/operations",
  RISK_COMPLIANCE: "/risk",
  MANAGEMENT: "/management",
};

export default function HomeRedirect() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading || !user) return; // AuthGate sends unauthenticated users to /login
    router.replace(ROLE_HOME[user.role] ?? "/agent");
  }, [user, loading, router]);

  return <div className="text-sm text-slate-500 py-10 text-center">Loading your dashboard...</div>;
}

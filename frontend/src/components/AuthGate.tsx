"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

const PUBLIC_PATHS = new Set(["/login"]);

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = PUBLIC_PATHS.has(pathname);

  useEffect(() => {
    if (!loading && !user && !isPublic) {
      router.replace("/login");
    }
  }, [loading, user, isPublic, router]);

  if (isPublic) return <>{children}</>;
  if (loading) return <div className="text-sm text-slate-500 py-10 text-center">Loading...</div>;
  if (!user) return null;
  return <>{children}</>;
}

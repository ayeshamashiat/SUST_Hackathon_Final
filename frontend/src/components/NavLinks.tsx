"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import type { UserRole } from "@/lib/types";

const ROLE_NAV: Record<UserRole, { href: string; label: string }[]> = {
  AGENT: [{ href: "/agent", label: "Your Outlet" }],
  FIELD_OFFICER: [
    { href: "/field-officer", label: "Field Dashboard" },
    { href: "/alerts", label: "Anomaly Review" },
  ],
  AREA_MANAGER: [{ href: "/management", label: "Area Overview" }],
  PROVIDER_OPS: [
    { href: "/operations", label: "Operations" },
    { href: "/alerts", label: "Anomaly Review" },
  ],
  RISK_COMPLIANCE: [
    { href: "/risk", label: "Risk Review" },
    { href: "/alerts", label: "Anomaly Review" },
  ],
  MANAGEMENT: [{ href: "/management", label: "Management" }],
};

export function NavLinks() {
  const { user } = useAuth();
  const pathname = usePathname();
  if (!user) return null;

  const links = ROLE_NAV[user.role] ?? [];

  return (
    <>
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={`transition-colors ${
            pathname === link.href ? "text-emerald-700 font-medium" : "hover:text-emerald-700"
          }`}
        >
          {link.label}
        </Link>
      ))}
    </>
  );
}

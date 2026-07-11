import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { AuthGate } from "@/components/AuthGate";
import { UserBadge } from "@/components/UserBadge";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Super Agent Liquidity Console",
  description: "Multi-provider liquidity, anomaly, and coordination prototype",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <AuthProvider>
          <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-10">
            <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold tracking-tight">Super Agent Console</span>
                <span className="text-xs text-slate-500 hidden sm:inline">
                  bKash &middot; Nagad &middot; Rocket - decision support, not a fraud verdict
                </span>
              </div>
              <nav className="flex items-center gap-4 text-sm">
                <Link href="/" className="hover:text-emerald-700 transition-colors">
                  Dashboard
                </Link>
                <Link href="/alerts" className="hover:text-emerald-700 transition-colors">
                  Anomaly Review
                </Link>
                <UserBadge />
              </nav>
            </div>
          </header>
          <main className="flex-1 mx-auto w-full max-w-6xl px-4 py-6">
            <AuthGate>{children}</AuthGate>
          </main>
          <footer className="border-t border-slate-200 px-4 py-3 text-center text-xs text-slate-500">
            Simulated data only &middot; advisory alerts, never an automated financial action &middot; human review
            required
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}

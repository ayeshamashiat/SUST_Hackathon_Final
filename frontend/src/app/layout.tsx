import type { Metadata } from "next";
<<<<<<< HEAD
import { Geist, Geist_Mono } from "next/font/google";
import { AuthGate } from "@/components/AuthGate";
import { NavLinks } from "@/components/NavLinks";
import { UserBadge } from "@/components/UserBadge";
=======
import { Geist_Mono, Plus_Jakarta_Sans } from "next/font/google";
import { AppShell } from "@/components/AppShell";
>>>>>>> d62e1759c36e9580ad46432e5fa3e2a264390af4
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Super Agent Console",
  description: "Multi-provider liquidity, anomaly, and coordination prototype",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${jakarta.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-slate-900">
        <AuthProvider>
<<<<<<< HEAD
          <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-10">
            <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold tracking-tight">Super Agent Console</span>
                <span className="text-xs text-slate-500 hidden sm:inline">
                  bKash &middot; Nagad &middot; Rocket - decision support, not a fraud verdict
                </span>
              </div>
              <nav className="flex items-center gap-4 text-sm">
                <NavLinks />
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
=======
          <AppShell>{children}</AppShell>
>>>>>>> d62e1759c36e9580ad46432e5fa3e2a264390af4
        </AuthProvider>
      </body>
    </html>
  );
}

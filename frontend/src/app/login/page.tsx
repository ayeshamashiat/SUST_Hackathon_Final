"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/");
    }
  }, [loading, user, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(username, password);
      router.replace("/");
    } catch (err) {
      setError(String(err instanceof Error ? err.message : err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="w-[380px]">
      <div className="rounded-[24px] border border-[#E8EAF0] bg-white p-9 shadow-[0_20px_40px_-24px_rgba(18,20,28,0.15)]">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-11 h-11 rounded-xl bg-accent-ink flex items-center justify-center shrink-0">
            <div className="w-[18px] h-[18px] rounded-[5px] bg-accent-light" />
          </div>
          <div>
            <div className="font-extrabold text-[15px] leading-tight">SUPER AGENT</div>
            <div className="font-semibold text-[11px] tracking-[0.14em] text-slate-400">CONSOLE</div>
          </div>
        </div>

        <h1 className="text-xl font-bold mb-1.5">Sign in</h1>
        <p className="text-[13px] text-slate-500 mb-6 leading-relaxed">
          Operations-team login only. Customers do not use this console.
        </p>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-xs text-slate-500 mb-1.5" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              placeholder="rafiq.officer"
              className="w-full rounded-[10px] border border-[#E3E6EE] bg-[#FAFBFD] px-3 py-2.5 text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              placeholder="••••••••"
              className="w-full rounded-[10px] border border-[#E3E6EE] bg-[#FAFBFD] px-3 py-2.5 text-sm"
              required
            />
          </div>

          {error && <p className="text-xs text-rose-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-1.5 rounded-xl bg-accent-ink px-3 py-3 text-sm font-semibold text-white hover:bg-[#272A36] transition-colors disabled:opacity-50"
          >
            {submitting ? "Signing in..." : "Log in"}
          </button>
        </form>

        <p className="text-[11px] text-slate-400 mt-5 leading-relaxed">
          Predetermined operations-hierarchy accounts only &middot; demo credentials via{" "}
          <code className="text-slate-500">docs/CREDENTIALS.md</code>
        </p>
      </div>
    </div>
  );
}

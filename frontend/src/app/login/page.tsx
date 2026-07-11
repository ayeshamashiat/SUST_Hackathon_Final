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
    <div className="mx-auto max-w-sm mt-16">
      <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
        <div>
          <h1 className="text-lg font-semibold">Super Agent Console</h1>
          <p className="text-sm text-slate-600 mt-1">
            Sign in with your operations-team login. Customers do not use this console.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              className="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm"
              required
            />
          </div>

          {error && <p className="text-xs text-rose-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-emerald-700 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
          >
            {submitting ? "Signing in..." : "Log in"}
          </button>
        </form>

        <p className="text-xs text-slate-400">
          Predetermined operations-hierarchy accounts only - see{" "}
          <code className="text-slate-500">docs/CREDENTIALS.md</code> for demo credentials.
        </p>
      </div>
    </div>
  );
}

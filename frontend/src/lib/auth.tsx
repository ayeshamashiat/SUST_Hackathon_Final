"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { clearSession, getStoredUser, getToken, setSession } from "./authStorage";
import { api } from "./api";
import type { AuthUser } from "./types";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    const stored = getStoredUser();
    if (!token || !stored) {
      setLoading(false);
      return;
    }
    // Trust the cached profile immediately, then quietly confirm the token is
    // still valid (not expired/revoked) - avoids a login flash on every reload.
    setUser(stored);
    api
      .me()
      .then((fresh) => {
        setUser(fresh);
        setSession(token, fresh);
      })
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const token = await api.login(username, password);
    const authUser: AuthUser = {
      username,
      role: token.role,
      display_name: token.display_name,
      agent_id: token.agent_id,
      provider_id: token.provider_id,
    };
    setSession(token.access_token, authUser);
    setUser(authUser);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

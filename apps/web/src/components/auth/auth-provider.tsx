"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const CSRF_COOKIE_NAME = process.env.NEXT_PUBLIC_CSRF_COOKIE_NAME ?? "csr_csrf";

export type AuthUser = {
  id: string;
  email: string;
  display_name: string;
  roles: string[];
  permissions: string[];
};

type AuthResponse = {
  user: AuthUser;
  csrf_token?: string;
  expires_at: string;
};

type AuthContextValue = {
  user: AuthUser | null;
  csrfToken: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function readCsrfCookie(): string | null {
  if (typeof document === "undefined") return null;
  const prefix = `${CSRF_COOKIE_NAME}=`;
  const match = document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith(prefix));
  return match ? decodeURIComponent(match.slice(prefix.length)) : null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const acceptResponse = useCallback((data: AuthResponse) => {
    setUser(data.user);
    setCsrfToken(data.csrf_token ?? readCsrfCookie());
    setError(null);
  }, []);

  useEffect(() => {
    let active = true;
    fetch(`${API_BASE}/auth/me`, { credentials: "include", cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("no-session");
        return (await response.json()) as AuthResponse;
      })
      .then((data) => {
        if (active) acceptResponse(data);
      })
      .catch(() => {
        if (active) {
          setUser(null);
          setCsrfToken(null);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [acceptResponse]);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = typeof data.detail === "string" ? data.detail : "Não foi possível iniciar sessão.";
      setError(message);
      throw new Error(message);
    }
    acceptResponse(data as AuthResponse);
  }, [acceptResponse]);

  const logout = useCallback(async () => {
    if (!csrfToken) throw new Error("Token de proteção da sessão indisponível.");
    const response = await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRF-Token": csrfToken },
    });
    if (!response.ok) throw new Error("Não foi possível terminar a sessão no servidor.");
    setUser(null);
    setCsrfToken(null);
  }, [csrfToken]);

  const value = useMemo(() => ({ user, csrfToken, loading, error, login, logout }), [
    user, csrfToken, loading, error, login, logout,
  ]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth deve ser utilizado dentro de AuthProvider.");
  return context;
}

"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/auth-provider";

export default function LoginPage() {
  const router = useRouter();
  const { login, error, loading, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setLocalError(null);
    try {
      await login(email, password);
      router.replace("/");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro ao iniciar sessão.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="auth-loading">A verificar sessão segura…</div>;
  if (user) return <div className="auth-loading">Sessão ativa. A abrir a plataforma…</div>;

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="auth-brand-mark">CS</div>
        <p className="panel-kicker">CLOUDSEC RANGE · PLATFORM CORE</p>
        <h1>Iniciar sessão</h1>
        <p className="auth-intro">Acede ao teu ambiente de aprendizagem e prática profissional.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="username"
            required
            maxLength={320}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="owner@example.local"
          />
          <label htmlFor="password">Palavra-passe</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="A tua palavra-passe"
          />
          {(localError || error) && <p className="auth-error" role="alert">{localError || error}</p>}
          <button className="auth-submit" type="submit" disabled={submitting}>
            {submitting ? "A autenticar…" : "Entrar com segurança"}
          </button>
        </form>
        <div className="auth-security-note">
          <span aria-hidden="true">⌑</span>
          Sessão protegida por cookie HttpOnly, expiração e controlo de acesso.
        </div>
      </section>
    </main>
  );
}

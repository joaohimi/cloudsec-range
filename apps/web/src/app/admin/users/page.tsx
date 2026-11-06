"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/auth/auth-provider";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type ManagedUser = {
  id: string; email: string; display_name: string; status: "active" | "disabled" | "pending";
  roles: string[]; created_at: string; last_login_at: string | null;
};
type UserList = { items: ManagedUser[]; total: number; limit: number; offset: number };

export default function UserManagementPage() {
  const { user, csrfToken } = useAuth();
  const [data, setData] = useState<UserList | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [roleCode, setRoleCode] = useState("learner");

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/users?limit=100&offset=0`, { credentials: "include", cache: "no-store" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Falha ao carregar utilizadores (${response.status}).`);
      setData(payload as UserList);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao carregar utilizadores.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadUsers(); }, [loadUsers]);

  async function mutate(url: string, method: string, body?: unknown) {
    if (!csrfToken) throw new Error("Token CSRF indisponível. Atualiza a sessão e tenta novamente.");
    const response = await fetch(`${API_BASE}${url}`, {
      method, credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `A operação falhou (${response.status}).`);
    return payload;
  }

  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(null); setSuccess(null);
    try {
      await mutate("/users", "POST", { email, display_name: name, password, role_codes: [roleCode] });
      setName(""); setEmail(""); setPassword(""); setRoleCode("learner");
      setSuccess("Conta criada. Entrega a palavra-passe inicial ao utilizador por um canal seguro.");
      await loadUsers();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível criar a conta."); }
    finally { setBusy(false); }
  }

  async function changeStatus(target: ManagedUser) {
    const nextStatus = target.status === "active" ? "disabled" : "active";
    if (!window.confirm(`Confirmas ${nextStatus === "disabled" ? "a desativação" : "a reativação"} de ${target.email}?`)) return;
    setBusy(true); setError(null); setSuccess(null);
    try {
      await mutate(`/users/${target.id}`, "PATCH", { status: nextStatus });
      setSuccess(`Estado de ${target.email} atualizado.`);
      await loadUsers();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível atualizar a conta."); }
    finally { setBusy(false); }
  }

  async function changeRole(target: ManagedUser, nextRole: string) {
    setBusy(true); setError(null); setSuccess(null);
    try {
      await mutate(`/users/${target.id}/roles`, "PUT", { role_codes: [nextRole] });
      setSuccess(`Função de ${target.email} atualizada.`);
      await loadUsers();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível atualizar a função."); }
    finally { setBusy(false); }
  }

  if (!user?.permissions.includes("users:manage")) {
    return <section className="panel admin-denied"><p className="eyebrow">PLATFORM CORE / ACCESS CONTROL</p><h1>Acesso restrito</h1><p>A tua conta não possui a permissão <code>users:manage</code>.</p></section>;
  }

  return (
    <div className="admin-users-page">
      <div className="page-heading"><div><p className="eyebrow">PLATFORM CORE / IDENTITY</p><h1>Gestão de utilizadores</h1><p className="page-description">Cria e administra contas, funções e estado de acesso. Contas não são apagadas: são desativadas para preservar histórico e auditoria.</p></div><span className="status-pill planned">M2 · User Management</span></div>
      {error ? <div className="form-alert error" role="alert">{error}</div> : null}
      {success ? <div className="form-alert success" role="status">{success}</div> : null}

      <section className="panel admin-create-panel">
        <div className="section-heading compact"><div><p className="eyebrow">NOVA IDENTIDADE</p><h2>Criar utilizador</h2></div></div>
        <form className="admin-user-form" onSubmit={createUser}>
          <label>Nome de apresentação<input value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={160} required autoComplete="name" /></label>
          <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} maxLength={320} required autoComplete="email" /></label>
          <label>Palavra-passe inicial<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={15} maxLength={128} required autoComplete="new-password" /><small>Mínimo 15 caracteres. Não é enviada por email nesta versão; entrega-a por um canal seguro.</small></label>
          <label>Função<select value={roleCode} onChange={(event) => setRoleCode(event.target.value)}><option value="learner">Learner — estudante</option><option value="reviewer">Reviewer — revisor técnico</option></select></label>
          <button className="button-primary" type="submit" disabled={busy || !csrfToken}>{busy ? "A processar…" : "Criar conta"}</button>
        </form>
        <p className="admin-security-note">A função Owner não pode ser atribuída nesta interface. A primeira conta administrativa permanece protegida pelo procedimento de bootstrap.</p>
      </section>

      <section className="panel admin-list-panel">
        <div className="section-heading compact"><div><p className="eyebrow">DIRECTORY</p><h2>Contas existentes</h2></div><span className="subtle-label">{data?.total ?? 0} conta(s)</span></div>
        {loading ? <p className="empty-state">A carregar contas…</p> : null}
        {!loading && data?.items.length === 0 ? <p className="empty-state">Ainda não existem contas.</p> : null}
        {data?.items.length ? <div className="admin-users-table-wrap"><table className="admin-users-table"><thead><tr><th>Utilizador</th><th>Função</th><th>Estado</th><th>Último login</th><th>Controlo</th></tr></thead><tbody>{data.items.map((item) => {
          const isOwner = item.roles.includes("owner");
          const isSelf = item.id === user.id;
          return <tr key={item.id}><td><strong>{item.display_name}</strong><small>{item.email}</small></td><td>{isOwner ? <span className="role-tag owner">Owner</span> : <select aria-label={`Função de ${item.email}`} value={item.roles.includes("reviewer") ? "reviewer" : "learner"} disabled={busy} onChange={(event) => void changeRole(item, event.target.value)}><option value="learner">Learner</option><option value="reviewer">Reviewer</option></select>}</td><td><span className={`status-pill ${item.status === "active" ? "success" : "planned"}`}>{item.status}</span></td><td>{item.last_login_at ? new Date(item.last_login_at).toLocaleString() : "Nunca"}</td><td>{isOwner || isSelf ? <span className="subtle-label">Protegida</span> : <button type="button" className="text-button" disabled={busy} onClick={() => void changeStatus(item)}>{item.status === "active" ? "Desativar" : "Reativar"}</button>}</td></tr>;
        })}</tbody></table></div> : null}
        <button className="button-secondary refresh-users" type="button" onClick={() => void loadUsers()} disabled={loading}>Atualizar lista</button>
      </section>
    </div>
  );
}

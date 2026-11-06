"use client";

import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import type { ReactNode } from "react";
import { useEffect } from "react";
import { useAuth } from "@/components/auth/auth-provider";

const navigation = [
  { href: "/", label: "Visão geral", icon: "⌂" },
  { href: "/learning", label: "Learning Center", icon: "▤" },
  { href: "/progress", label: "O meu progresso", icon: "◴" },
  { href: "/internship", label: "Internship Center", icon: "▣" },
  { href: "/labs", label: "Laboratórios", icon: "⌘" },
  { href: "/assessments", label: "Avaliações", icon: "✓" },
  { href: "/portfolio", label: "Portfólio", icon: "▧" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const isLogin = pathname === "/login";

  useEffect(() => {
    if (loading) return;
    if (!user && !isLogin) router.replace("/login");
    if (user && isLogin) router.replace("/");
  }, [loading, user, isLogin, router]);

  if (loading || (!user && !isLogin) || (user && isLogin)) {
    return <div className="auth-loading">{loading ? "A verificar sessão segura…" : "A preparar o teu espaço de trabalho…"}</div>;
  }

  if (isLogin) return <>{children}</>;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="CloudSec Range - início">
          <span className="brand-mark">CS</span>
          <span className="brand-copy">
            <strong>CloudSec Range</strong>
            <small>Academy & Cyber Range</small>
          </span>
        </Link>

        <div className="workspace-label">WORKSPACE</div>
        <nav className="navigation" aria-label="Navegação principal">
          {navigation.filter((item) => item.href !== "/progress" || user?.permissions.includes("learning:read")).map((item) => (
            <Link key={item.href} href={item.href} className={`nav-item${(item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)) ? " active" : ""}`}>
              <span className="nav-icon" aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
          {user?.permissions.includes("assessments:review") ? <Link href="/reviews" className={`nav-item${pathname.startsWith("/reviews") ? " active" : ""}`}><span className="nav-icon" aria-hidden="true">✓</span><span>Revisão técnica</span></Link> : null}
          {user?.permissions.includes("users:manage") ? <Link href="/admin/users" className={`nav-item${pathname.startsWith("/admin/users") ? " active" : ""}`}><span className="nav-icon" aria-hidden="true">♙</span><span>Utilizadores</span></Link> : null}
        </nav>

        <div className="sidebar-bottom">
          <div className="environment-card">
            <span className="status-dot" />
            <div>
              <strong>Ambiente local</strong>
              <small>Desenvolvimento · v0.4.0</small>
            </div>
          </div>
          <p className="sidebar-note">Formação completa. Prática profissional. Competência demonstrada.</p>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">CLOUDSEC RANGE <span>/</span> WORKSPACE</div>
          <div className="topbar-right">
            <span className="local-badge"><span className="status-dot" /> Local</span>
            <span className="topbar-user">{user?.display_name}</span>
            <button className="logout-button" type="button" onClick={() => void logout().catch(() => window.alert("Não foi possível terminar a sessão. Tenta novamente."))}>Terminar sessão</button>
          </div>
        </header>
        <div className="page-content">{children}</div>
        <footer className="footer">CloudSec Range <span>·</span> Ambiente de aprendizagem e estágio simulado <span>·</span> v0.4.0</footer>
      </main>
    </div>
  );
}

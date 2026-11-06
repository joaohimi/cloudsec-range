import { getSessionCookieHeader } from "@/lib/server-session";
import Link from "next/link";

export const dynamic = "force-dynamic";
const API_BASE = (process.env.API_INTERNAL_URL ?? "http://localhost:8000").replace(/\/$/, "");

type Ticket = {
  id: string; ticket_key: string; title: string; department: string; priority: string; status: string;
  description: string; business_impact: string | null; asset_context: string | null;
  assigned_role: string | null; initial_state: string | null; investigation_steps: string[];
  execution_steps: string[]; validation_steps: string[]; safety_scope: string | null;
  acceptance_criteria: string[]; module_code: string | null; module_title: string | null;
};

async function getTickets(): Promise<{ count: number; tickets: Ticket[] } | null> {
  try {
    const sessionCookie = await getSessionCookieHeader();
    const response = await fetch(`${API_BASE}/api/v1/curriculum/tickets`, {
      cache: "no-store",
      headers: sessionCookie ? { cookie: sessionCookie } : undefined,
    });
    if (!response.ok) return null;
    return (await response.json()) as { count: number; tickets: Ticket[] };
  } catch { return null; }
}

function Steps({ title, items }: { title: string; items: string[] }) {
  return <div className="ticket-subsection"><h4>{title}</h4><ol>{items.map((item, index) => <li key={index}>{item}</li>)}</ol></div>;
}

export default async function InternshipPage() {
  const result = await getTickets();
  return (
    <div className="section-page internship-page">
      <div className="page-heading learning-heading">
        <div><p className="eyebrow">COMPANY / INTERNSHIP</p><h1>Internship Center</h1><p className="page-description">Nexus Digital Services — ambiente profissional simulado com pedidos, incidentes, alterações, critérios de aceitação, validação e revisão técnica. Cada tarefa está ligada às competências do Learning Center.</p></div>
        <span className="status-pill planned">Empresa simulada</span>
      </div>
      <section className="module-notice panel"><p className="panel-kicker">MODELO DE OPERAÇÃO</p><h2>Aprender e executar sobre o mesmo mapa de competências.</h2><p>Os tickets não são exercícios vagos. Cada tarefa deve indicar contexto de negócio, função, ativo, estado inicial, investigação, execução, validação, critérios de aceitação, âmbito de segurança e evidências. A simulação não substitui experiência profissional real.</p></section>
      {!result ? <section className="panel learning-unavailable"><h2>Não foi possível carregar os tickets.</h2><p>Confirma se a API está ativa e consulta <code>/docs</code> para verificar a rota.</p></section> : <>
        <div className="learning-stats"><article className="panel learning-stat"><span>Tickets registados</span><strong>{result.count}</strong><small>Associados ao currículo</small></article><article className="panel learning-stat"><span>Tickets em backlog</span><strong>{result.tickets.filter((ticket) => ticket.status === "backlog").length}</strong><small>Aguardam execução do formando</small></article><article className="panel learning-stat"><span>Empresa</span><strong>Nexus</strong><small>Ambiente fictício persistente</small></article><article className="panel learning-stat"><span>Política</span><strong>Scope</strong><small>Sem acesso a ativos externos</small></article></div>
        {result.tickets.length === 0 ? <section className="panel roadmap-panel"><h2>Ainda não existem tickets.</h2><p>Os tickets serão criados quando forem associados a competências e módulos.</p></section> : <div className="module-stack">{result.tickets.map((ticket) => <article className="panel ticket-card" key={ticket.id}>
          <div className="ticket-topline"><span>{ticket.ticket_key}</span><span>{ticket.department}</span><span>Prioridade: {ticket.priority}</span><span>Estado: {ticket.status}</span></div>
          <h3>{ticket.title}</h3><p>{ticket.description}</p>
          {ticket.business_impact ? <div className="ticket-impact"><strong>Impacto de negócio</strong><p>{ticket.business_impact}</p></div> : null}
          <div className="ticket-facts"><div><small>Ativo / contexto</small><p>{ticket.asset_context}</p></div><div><small>Função atribuída</small><p>{ticket.assigned_role}</p></div><div><small>Estado inicial</small><p>{ticket.initial_state}</p></div></div>
          <Steps title="Investigação" items={ticket.investigation_steps} />
          <Steps title="Execução" items={ticket.execution_steps} />
          <Steps title="Validação" items={ticket.validation_steps} />
          <Steps title="Critérios de aceitação" items={ticket.acceptance_criteria} />
          <div className="safety-strip"><strong>Âmbito de segurança</strong><p>{ticket.safety_scope}</p></div>
          {ticket.module_code ? <Link href={`/learning/${ticket.module_code}`} className="text-link ticket-module-link">Ver aulas e competências associadas → {ticket.module_title}</Link> : null}
        </article>)}</div>}
      </>}
    </div>
  );
}

import { getSessionCookieHeader } from "@/lib/server-session";
import Link from "next/link";
import { ModuleProgressPanel } from "@/components/learning/module-progress-panel";
import type { ReactNode } from "react";

export const dynamic = "force-dynamic";
const API_BASE = (process.env.API_INTERNAL_URL ?? "http://localhost:8000").replace(/\/$/, "");

type Competency = { id: string; code: string; title: string; description: string; is_security_relevant: boolean };
type Lesson = { id: string; code: string; title: string; sequence: number; summary: string | null; content_markdown: string | null; status: string };
type LabStep = { title: string; shell?: string; commands?: string[]; expected?: string; why?: string };
type Lab = {
  id: string; code: string; title: string; description: string | null; status: string;
  safety_profile: string; environment: string; estimated_minutes: number | null;
  manifest: { objective?: string; safety?: Record<string, unknown>; steps?: LabStep[]; independent_tasks?: string[]; deliverables?: string[]; cleanup?: string };
};
type Ticket = {
  id: string; ticket_key: string; title: string; department: string; priority: string; status: string;
  description: string; business_impact: string | null; asset_context: string | null;
  assigned_role: string | null; initial_state: string | null; investigation_steps: string[];
  execution_steps: string[]; validation_steps: string[]; safety_scope: string | null; acceptance_criteria: string[];
};
type AssessmentQuestion = { id: string; points: number; type: string; prompt: string };
type AssessmentRubric = {
  duration_minutes?: number; instructions?: string; questions?: AssessmentQuestion[];
  scoring_rubric?: { criterion: string; points: number; description: string }[];
  critical_errors?: string[]; mastery_rule?: string; feedback_policy?: string;
};
type Assessment = {
  id: string; code: string; title: string; assessment_type: string; status: string;
  total_points: number; mastery_threshold: number; rubric: AssessmentRubric;
};
type Topic = { id: string; code: string; title: string; position: number; description?: string | null };
type Resource = { id: string; title: string; resource_type: string; url: string; publisher: string | null; product_version: string | null };
type ModuleDetail = {
  id: string; code: string; source_module_code: string | null; title: string; position: number;
  estimated_hours: number | null; content_status: string; block: string | null;
  competencies: Competency[]; lessons: Lesson[]; labs: Lab[]; tickets: Ticket[];
  assessments: Assessment[]; topics: Topic[]; resources: Resource[];
};

async function getModule(code: string): Promise<ModuleDetail | null> {
  try {
    const sessionCookie = await getSessionCookieHeader();
    const response = await fetch(`${API_BASE}/api/v1/curriculum/modules/${encodeURIComponent(code)}`, {
      cache: "no-store",
      headers: sessionCookie ? { cookie: sessionCookie } : undefined,
    });
    if (!response.ok) return null;
    return (await response.json()) as ModuleDetail;
  } catch { return null; }
}

function inline(text: string): ReactNode[] {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean).map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    return <span key={index}>{part}</span>;
  });
}

function MarkdownContent({ source }: { source: string | null }) {
  if (!source) return <p className="empty-state">Conteúdo não disponível.</p>;
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i += 1; continue; }
    if (line.startsWith("```")) {
      const code: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("```")) code.push(lines[i++]);
      i += 1;
      blocks.push(<pre className="lesson-code" key={`code-${i}`}><code>{code.join("\n")}</code></pre>);
      continue;
    }
    if (/^\|.*\|$/.test(line)) {
      const tableLines: string[] = [];
      while (i < lines.length && /^\|.*\|$/.test(lines[i])) tableLines.push(lines[i++]);
      const rows = tableLines.map((row) => row.split("|").slice(1, -1).map((cell) => cell.trim()));
      const body = rows.filter((row) => !row.every((cell) => /^:?-{3,}:?$/.test(cell)));
      const header = body[0] ?? [];
      blocks.push(<div className="lesson-table-wrap" key={`table-${i}`}><table className="lesson-table"><thead><tr>{header.map((cell, n) => <th key={n}>{inline(cell)}</th>)}</tr></thead><tbody>{body.slice(1).map((row, r) => <tr key={r}>{row.map((cell, n) => <td key={n}>{inline(cell)}</td>)}</tr>)}</tbody></table></div>);
      continue;
    }
    if (line.startsWith("### ")) { blocks.push(<h4 key={`h4-${i++}`}>{inline(line.slice(4))}</h4>); continue; }
    if (line.startsWith("## ")) { blocks.push(<h3 key={`h3-${i++}`}>{inline(line.slice(3))}</h3>); continue; }
    if (line.startsWith("# ")) { blocks.push(<h2 key={`h2-${i++}`}>{inline(line.slice(2))}</h2>); continue; }
    if (/^-\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^-\s+/.test(lines[i])) items.push(lines[i++].replace(/^-\s+/, ""));
      blocks.push(<ul key={`ul-${i}`}>{items.map((item, n) => <li key={n}>{inline(item)}</li>)}</ul>);
      continue;
    }
    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) items.push(lines[i++].replace(/^\d+\.\s+/, ""));
      blocks.push(<ol key={`ol-${i}`}>{items.map((item, n) => <li key={n}>{inline(item)}</li>)}</ol>);
      continue;
    }
    const paragraph = [line];
    i += 1;
    while (i < lines.length && lines[i].trim() && !/^(#{1,3}\s|```|\|.*\||-\s+|\d+\.\s+)/.test(lines[i])) paragraph.push(lines[i++]);
    blocks.push(<p key={`p-${i}`}>{inline(paragraph.join(" "))}</p>);
  }
  return <div className="lesson-content">{blocks}</div>;
}

function ArraySection({ title, items }: { title: string; items: string[] }) {
  return <div className="ticket-subsection"><h4>{title}</h4>{items.length ? <ol>{items.map((item, index) => <li key={index}>{item}</li>)}</ol> : <p className="empty-state">Ainda não definido.</p>}</div>;
}

export default async function ModulePage({ params }: { params: Promise<{ moduleCode: string }> }) {
  const { moduleCode } = await params;
  const module = await getModule(moduleCode);
  if (!module) return <div className="section-page"><p className="eyebrow">LEARNING CENTER</p><h1>Módulo não encontrado</h1><p className="page-description">O código pedido não existe no mapa curricular importado ou a API está indisponível.</p><Link href="/learning" className="text-link">← Voltar ao currículo</Link></div>;

  const moduleStatus = module.content_status === "draft" ? "Conteúdo em revisão" : module.content_status === "ready" ? "Preparado para avaliação" : module.content_status === "not_authored" ? "Conteúdo por elaborar" : module.content_status;

  return (
    <div className="learning-module-page">
      <Link href="/learning" className="text-link">← Voltar ao mapa curricular</Link>
      <div className="page-heading learning-heading module-page-heading">
        <div><p className="eyebrow">LEARNING CENTER / {module.block ?? "MÓDULO"} / {module.source_module_code}</p><h1>{module.title}</h1><p className="page-description">Código interno: {module.code} · Carga horária original: {module.estimated_hours ?? "—"} horas · Unidade editorial: 1.0.0.</p></div>
        <span className="status-pill planned">{moduleStatus}</span>
      </div>

      <section className="module-notice panel"><p className="panel-kicker">ESTADO EDITORIAL E CRITÉRIO DE DOMÍNIO</p><h2>Conteúdo inicial preparado; competência ainda não validada.</h2><p>As aulas, o inventário e o ticket já estão estruturados. Isto não significa que o módulo esteja concluído: ainda tens de estudar, executar os laboratórios, resolver o ticket, realizar a avaliação e apresentar evidências para revisão técnica. Os estados só avançam com demonstração real de competência.</p></section>
      <ModuleProgressPanel moduleCode={module.code} assessments={module.assessments.map((item) => ({ id: item.id, code: item.code, title: item.title, rubric: item.rubric }))} />

      <section className="module-section"><div className="module-section-heading"><div><p className="panel-kicker">MAPA DE APRENDIZAGEM</p><h2>Tópicos e competências</h2></div><span>{module.topics.length} tópicos · {module.competencies.length} competências</span></div>
        <div className="traceability-grid">
          <article className="panel traceability-card"><div className="traceability-card-head"><h3>Tópicos do módulo</h3><strong>{module.topics.length}</strong></div><ol>{module.topics.map((topic) => <li key={topic.id}><strong>{topic.code}</strong> · {topic.title}</li>)}</ol></article>
          <article className="panel traceability-card"><div className="traceability-card-head"><h3>Competências demonstráveis</h3><strong>{module.competencies.length}</strong></div><ul>{module.competencies.map((competency) => <li key={competency.id}><strong>{competency.code}</strong> · {competency.title}<p>{competency.description}</p>{competency.is_security_relevant ? <span className="module-tag">Relevância de segurança</span> : null}</li>)}</ul></article>
        </div>
      </section>

      <section className="module-section"><div className="module-section-heading"><div><p className="panel-kicker">LEARNING CENTER</p><h2>Aulas completas</h2></div><span>{module.lessons.length} aulas</span></div>
        <div className="module-stack">{module.lessons.map((lesson) => <article className="panel lesson-card" key={lesson.id}>
          <div className="lesson-card-head"><div><p className="panel-kicker">AULA {String(lesson.sequence).padStart(2, "0")} · {lesson.code}</p><h3>{lesson.title}</h3><p>{lesson.summary}</p></div><span className="status-pill planned">{lesson.status === "draft" ? "Rascunho para revisão" : lesson.status}</span></div>
          <MarkdownContent source={lesson.content_markdown} />
        </article>)}</div>
      </section>

      <section className="module-section"><div className="module-section-heading"><div><p className="panel-kicker">LABORATORY ENGINE</p><h2>Laboratórios guiados</h2></div><span>{module.labs.length} laboratórios planeados</span></div>
        <div className="module-stack">{module.labs.map((lab) => <article className="panel lab-card" key={lab.id}>
          <div className="lesson-card-head"><div><p className="panel-kicker">{lab.code} · {lab.environment} · {lab.estimated_minutes ?? "—"} min</p><h3>{lab.title}</h3><p>{lab.description}</p></div><span className="status-pill planned">{lab.status}</span></div>
          {lab.manifest.objective ? <p className="lab-objective"><strong>Objetivo:</strong> {lab.manifest.objective}</p> : null}
          {lab.manifest.safety ? <div className="safety-strip"><strong>Perfil de segurança: {lab.safety_profile}</strong><p>Alterações de sistema: {String(lab.manifest.safety.changes_system)} · Requer sudo: {String(lab.manifest.safety.requires_sudo)} · Acesso à rede: {String(lab.manifest.safety.network_access)}</p><p>{String(lab.manifest.safety.allowed_scope ?? "Âmbito local controlado.")}</p></div> : null}
          {lab.manifest.steps?.map((step, index) => <div className="lab-step" key={`${lab.code}-${index}`}><h4>{index + 1}. {step.title}</h4>{step.shell ? <p className="subtle-label">Executar em: {step.shell}</p> : null}{step.commands?.map((command, commandIndex) => <pre className="lesson-code" key={commandIndex}><code>{command}</code></pre>)}{step.expected ? <p><strong>Resultado a observar:</strong> {step.expected}</p> : null}{step.why ? <p><strong>Porquê:</strong> {step.why}</p> : null}</div>)}
          {lab.manifest.independent_tasks ? <ArraySection title="Exercício individual" items={lab.manifest.independent_tasks} /> : null}
          {lab.manifest.deliverables ? <ArraySection title="Entregáveis" items={lab.manifest.deliverables} /> : null}
          {lab.manifest.cleanup ? <p className="lab-cleanup"><strong>Limpeza:</strong> {lab.manifest.cleanup}</p> : null}
        </article>)}</div>
      </section>

      <section className="module-section internship-module-section"><div className="module-section-heading"><div><p className="panel-kicker">INTERNSHIP CENTER · NEXUS DIGITAL SERVICES</p><h2>Trabalho profissional simulado</h2></div><span>{module.tickets.length} ticket(s)</span></div>
        <p className="internship-disclaimer">A empresa, os ativos e o cenário são fictícios. O ambiente WSL local é o alvo de treino declarado; não o apresentes como infraestrutura real de produção.</p>
        {module.tickets.map((ticket) => <article className="panel ticket-card" key={ticket.id}>
          <div className="ticket-topline"><span>{ticket.ticket_key}</span><span>{ticket.department}</span><span>Prioridade: {ticket.priority}</span><span>Estado: {ticket.status}</span></div>
          <h3>{ticket.title}</h3><p>{ticket.description}</p>
          {ticket.business_impact ? <div className="ticket-impact"><strong>Impacto de negócio</strong><p>{ticket.business_impact}</p></div> : null}
          <div className="ticket-facts"><div><small>Ativo e âmbito</small><p>{ticket.asset_context}</p></div><div><small>Função atribuída</small><p>{ticket.assigned_role}</p></div><div><small>Estado inicial</small><p>{ticket.initial_state}</p></div></div>
          <ArraySection title="Investigação" items={ticket.investigation_steps} />
          <ArraySection title="Execução" items={ticket.execution_steps} />
          <ArraySection title="Validação" items={ticket.validation_steps} />
          <ArraySection title="Critérios de aceitação" items={ticket.acceptance_criteria} />
          <div className="safety-strip"><strong>Âmbito e segurança</strong><p>{ticket.safety_scope}</p></div>
        </article>)}
      </section>

      <section className="module-section"><div className="module-section-heading"><div><p className="panel-kicker">ASSESSMENT ENGINE</p><h2>Avaliação e critérios de domínio</h2></div><span>{module.assessments.length} avaliação(ões)</span></div>
        {module.assessments.map((assessment) => <article className="panel assessment-card" key={assessment.id}>
          <div className="lesson-card-head"><div><p className="panel-kicker">{assessment.code} · {assessment.assessment_type.toUpperCase()}</p><h3>{assessment.title}</h3><p>{assessment.rubric.instructions}</p></div><span className="status-pill planned">{assessment.total_points} pontos · domínio {assessment.mastery_threshold}%</span></div>
          <div className="assessment-questions"><h4>Perguntas</h4>{assessment.rubric.questions?.map((question) => <div className="assessment-question" key={question.id}><span>{question.id} · {question.points} pontos</span><p>{question.prompt}</p></div>)}</div>
          <div className="assessment-rubric"><h4>Grelha de avaliação</h4>{assessment.rubric.scoring_rubric?.map((item) => <div className="rubric-row" key={item.criterion}><div><strong>{item.criterion}</strong><p>{item.description}</p></div><b>{item.points}</b></div>)}</div>
          {assessment.rubric.critical_errors?.length ? <div className="critical-errors"><h4>Erros críticos que impedem domínio</h4><ul>{assessment.rubric.critical_errors.map((item) => <li key={item}>{item}</li>)}</ul></div> : null}
          {assessment.rubric.mastery_rule ? <p className="mastery-rule"><strong>Regra de domínio:</strong> {assessment.rubric.mastery_rule}</p> : null}
          {assessment.rubric.feedback_policy ? <p className="mastery-rule"><strong>Política de correção:</strong> {assessment.rubric.feedback_policy}</p> : null}
        </article>)}
        <p className="assessment-note">A plataforma armazena tentativas e notas, mas esta avaliação é corrigida após revisão técnica. Não existe correção automática das respostas nesta versão.</p>
      </section>

      <section className="module-section"><div className="module-section-heading"><div><p className="panel-kicker">DOCUMENTAÇÃO OFICIAL</p><h2>Referências para estudo</h2></div><span>{module.resources.length} referências</span></div>
        <div className="resource-list panel">{module.resources.map((resource) => <a className="resource-row" href={resource.url} target="_blank" rel="noreferrer" key={resource.id}><div><strong>{resource.title}</strong><small>{resource.publisher ?? "Publicador não indicado"} · {resource.product_version ?? "Versão online"}</small></div><span>Consultar ↗</span></a>)}</div>
      </section>
    </div>
  );
}

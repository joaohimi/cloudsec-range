import { getSessionCookieHeader } from "@/lib/server-session";
import Link from "next/link";

export const dynamic = "force-dynamic";

const API_BASE = (process.env.API_INTERNAL_URL ?? "http://localhost:8000").replace(/\/$/, "");

type Module = {
  id: string;
  code: string;
  source_module_code: string | null;
  title: string;
  position: number;
  estimated_hours: number | null;
  content_status: string;
  source_verified: boolean;
  competency_count: number;
  lesson_count: number;
  lab_count: number;
  ticket_count: number;
  assessment_count: number;
};

type Block = { id: string; code: string; title: string; position: number; modules: Module[] };
type Track = {
  id: string;
  code: string;
  title: string;
  description: string | null;
  position: number;
  blocks: Block[];
  environment_labs: { id: string; code: string; title: string; estimated_minutes: number | null; status: string }[];
};
type Catalog = {
  version: { code: string; title: string; source_filename: string; status: string } | null;
  summary: { tracks: number; blocks: number; modules: number; estimated_module_hours: number; competencies: number; lessons: number; labs: number; tickets: number; assessments: number };
  tracks: Track[];
  integrity: { canonical_order_preserved: boolean; content_authored: boolean; note: string };
};

async function getCatalog(): Promise<Catalog | null> {
  try {
    const sessionCookie = await getSessionCookieHeader();
    const response = await fetch(`${API_BASE}/api/v1/curriculum/catalog`, {
      cache: "no-store",
      headers: sessionCookie ? { cookie: sessionCookie } : undefined,
    });
    if (!response.ok) return null;
    return (await response.json()) as Catalog;
  } catch {
    return null;
  }
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    not_authored: "Conteúdo por elaborar",
    draft: "Rascunho",
    in_review: "Em revisão",
    ready: "Preparado",
    verified: "Validado",
  };
  return labels[status] ?? status;
}

export default async function LearningPage() {
  const catalog = await getCatalog();

  return (
    <div className="learning-page">
      <div className="page-heading learning-heading">
        <div>
          <p className="eyebrow">ACADEMY / LEARNING</p>
          <h1>Learning Center</h1>
          <p className="page-description">O teu mapa original, convertido numa estrutura curricular versionada. Cada módulo será desenvolvido com teoria, documentação oficial, prática, troubleshooting, avaliação e evidência.</p>
        </div>
        <span className="status-pill planned">Currículo importado</span>
      </div>

      {!catalog ? (
        <section className="panel learning-unavailable">
          <p className="panel-kicker">API INDISPONÍVEL</p>
          <h2>Não foi possível carregar o currículo.</h2>
          <p>Confirma se os serviços `api` e `db` estão ativos e se a migração do Curriculum Engine foi aplicada.</p>
          <code>docker compose ps</code>
        </section>
      ) : (
        <>
          <section className="learning-source panel">
            <div>
              <p className="panel-kicker">FONTE CANÓNICA · {catalog.version?.code ?? "sem versão ativa"}</p>
              <h2>{catalog.version?.title ?? "Mapa curricular"}</h2>
              <p>{catalog.version?.source_filename ?? "Fonte não registada"}</p>
            </div>
            <div className="source-check"><span className="status-dot" /> Ordem e identificadores preservados</div>
          </section>

          <div className="learning-stats">
            <article className="panel learning-stat"><span>Trilhas</span><strong>{catalog.summary.tracks}</strong><small>Linux e Networking</small></article>
            <article className="panel learning-stat"><span>Blocos / fases</span><strong>{catalog.summary.blocks}</strong><small>Sequência original</small></article>
            <article className="panel learning-stat"><span>Módulos</span><strong>{catalog.summary.modules}</strong><small>Sem contar o Lab 0</small></article>
            <article className="panel learning-stat"><span>Horas dos módulos</span><strong>{catalog.summary.estimated_module_hours}h</strong><small>Lab 0: 6h adicionais</small></article>
          </div>

          <div className="learning-progress panel">
            <div>
              <p className="panel-kicker">ESTADO REAL DO CONTEÚDO</p>
              <h2>{catalog.summary.lessons} aulas publicadas de momento</h2>
              <p>Importar o mapa não significa que as aulas já estejam escritas. Nenhum módulo será apresentado como dominado sem prática e evidências verificáveis.</p>
            </div>
            <div className="progress-metrics">
              <div><strong>{catalog.summary.competencies}</strong><span>Competências</span></div>
              <div><strong>{catalog.summary.labs}</strong><span>Laboratórios</span></div>
              <div><strong>{catalog.summary.tickets}</strong><span>Tickets</span></div>
              <div><strong>{catalog.summary.assessments}</strong><span>Avaliações</span></div>
            </div>
          </div>

          {catalog.tracks.map((track) => {
            const modules = track.blocks.reduce((total, block) => total + block.modules.length, 0);
            const hours = track.blocks.reduce((total, block) => total + block.modules.reduce((subtotal, module) => subtotal + (module.estimated_hours ?? 0), 0), 0);
            return (
              <section className="learning-track" key={track.id}>
                <div className="learning-track-heading">
                  <div><p className="panel-kicker">TRILHA {String(track.position).padStart(2, "0")}</p><h2>{track.title}</h2><p>{track.description}</p></div>
                  <div className="track-total"><strong>{modules}</strong><span>módulos</span><strong>{hours}h</strong><span>estimadas</span></div>
                </div>
                <div className="learning-blocks">
                  {track.blocks.map((block) => (
                    <article className="panel learning-block" key={block.id}>
                      <div className="block-heading"><span>{block.code}</span><small>{block.modules.length} {block.modules.length === 1 ? "módulo" : "módulos"}</small></div>
                      <div className="module-list">
                        {block.modules.map((module) => (
                          <Link href={`/learning/${module.code}`} className="module-row" key={module.id}>
                            <span className="module-code">{module.source_module_code}</span>
                            <span className="module-main"><strong>{module.title}</strong><small>{statusLabel(module.content_status)}</small></span>
                            <span className="module-hours">{module.estimated_hours}h</span>
                            <span className="module-arrow">→</span>
                          </Link>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
                {track.environment_labs.map((lab) => (
                  <div className="environment-lab panel" key={lab.id}>
                    <span className="lab-icon">⌘</span><div><small>LABORATÓRIO DE AMBIENTE · {lab.code}</small><strong>{lab.title}</strong><span>{Math.round((lab.estimated_minutes ?? 0) / 60)}h · {lab.status === "planned" ? "Planeado" : lab.status}</span></div>
                  </div>
                ))}
              </section>
            );
          })}

          <p className="learning-integrity-note">{catalog.integrity.note}</p>
        </>
      )}
    </div>
  );
}

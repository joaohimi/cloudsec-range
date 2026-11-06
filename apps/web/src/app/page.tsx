import Link from "next/link";
import { getSessionCookieHeader } from "@/lib/server-session";

type ApiHealth = { status: string; checks?: { database?: string; redis?: string } };
type LearnerProgress = { summary: { competencies_mastered: number; competencies_total: number; labs_validated: number; labs_total: number; lessons_completed: number; lessons_total: number; assessments_passed: number; assessment_attempts: number } };

async function getApiHealth(): Promise<ApiHealth> {
  const baseUrl = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${baseUrl}/health/ready`, { cache: "no-store" });
    return (await response.json()) as ApiHealth;
  } catch {
    return { status: "não ligado" };
  }
}

async function getLearnerProgress(): Promise<LearnerProgress | null> {
  const baseUrl = (process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  try {
    const cookie = await getSessionCookieHeader();
    const response = await fetch(`${baseUrl}/api/v1/learning/me/progress`, {
      cache: "no-store", headers: cookie ? { cookie } : undefined,
    });
    if (!response.ok) return null;
    return (await response.json()) as LearnerProgress;
  } catch { return null; }
}

const areas = [
  { number: "01", title: "Fundamentos de infraestrutura", topics: "Linux · Networking · Armazenamento · Sistemas", tag: "Fundamentos" },
  { number: "02", title: "Programação e controlo de versões", topics: "Python · Git · GitHub", tag: "Automação" },
  { number: "03", title: "Infraestrutura e entrega segura", topics: "DevOps necessário · Containers · IaC · CI/CD", tag: "Infraestrutura" },
  { number: "04", title: "Cloud Computing", topics: "AWS · IAM · VPC · Compute · Storage", tag: "Cloud" },
  { number: "05", title: "DevSecOps", topics: "SAST · SCA · DAST · Secrets · Pipeline Security", tag: "App & Pipeline Security" },
  { number: "06", title: "Cloud Security", topics: "IAM · Network · Data · Detection · Incident Response", tag: "Especialização" },
  { number: "07", title: "Cloud Security Architecture", topics: "Zero Trust · Landing Zones · Governance · Resilience", tag: "Arquitetura" },
];

export default async function DashboardPage() {
  const [api, progress] = await Promise.all([getApiHealth(), getLearnerProgress()]);
  const apiReady = api.status === "ready";
  const databaseReady = api.checks?.database === "ok";
  const redisReady = api.checks?.redis === "ok";

  return (
    <div className="dashboard-page">
      <section className="hero panel">
        <div className="hero-copy">
          <p className="eyebrow">PERSONAL CLOUD SECURITY TRAINING ENVIRONMENT</p>
          <h1>Aprender. Praticar.<br /><span>Demonstrar competência.</span></h1>
          <p className="hero-description">Um ambiente integrado de formação e estágio profissional simulado, desde os fundamentos de infraestrutura até Cloud Security.</p>
          <div className="hero-actions">
            <Link href="/learning" className="button-primary">Abrir Learning Center <span>→</span></Link>
            <Link href="/internship" className="button-secondary">Ver estágio simulado</Link>
            <Link href="/progress" className="button-secondary">O meu progresso</Link>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="orb orb-one" />
          <div className="orb orb-two" />
          <div className="shield-visual"><span>CS</span><small>RANGE</small></div>
          <div className="visual-caption"><span className="status-dot" /> ISOLATED TRAINING ENVIRONMENT</div>
        </div>
      </section>

      <section className="stats-grid" aria-label="Indicadores de progresso">
        <article className="stat-card panel"><span className="stat-label">Competências dominadas</span><strong>{progress?.summary.competencies_mastered ?? "—"}</strong><small>{progress ? `De ${progress.summary.competencies_total} competências` : "Progresso indisponível"}</small></article>
        <article className="stat-card panel"><span className="stat-label">Laboratórios validados</span><strong>{progress?.summary.labs_validated ?? "—"}</strong><small>{progress ? `De ${progress.summary.labs_total} laboratórios` : "Progresso indisponível"}</small></article>
        <article className="stat-card panel"><span className="stat-label">Aulas concluídas</span><strong>{progress?.summary.lessons_completed ?? "—"}</strong><small>{progress ? `De ${progress.summary.lessons_total} aulas` : "Progresso indisponível"}</small></article>
        <article className="stat-card panel"><span className="stat-label">Avaliações aprovadas</span><strong>{progress?.summary.assessments_passed ?? "—"}</strong><small>{progress ? `${progress.summary.assessment_attempts} tentativas registadas` : "Progresso indisponível"}</small></article>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <div><p className="eyebrow">PERCURSO DE FORMAÇÃO</p><h2>Da infraestrutura à Cloud Security</h2></div>
          <span className="subtle-label">Estrutura de alto nível · não substitui o mapa original</span>
        </div>
        <div className="area-grid">
          {areas.map((area) => (
            <article className="area-card panel" key={area.number}>
              <div className="area-card-top"><span className="area-number">{area.number}</span><span className="area-tag">{area.tag}</span></div>
              <h3>{area.title}</h3>
              <p>{area.topics}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="bottom-grid">
        <article className="panel status-panel">
          <div className="section-heading compact"><div><p className="eyebrow">ESTADO DA PLATAFORMA</p><h2>Serviços locais</h2></div></div>
          <div className="service-row"><span><i className="service-indicator" /> Frontend</span><strong className="service-ok">Online</strong></div>
          <div className="service-row"><span><i className={`service-indicator ${apiReady ? "" : "offline"}`} /> API</span><strong className={apiReady ? "service-ok" : "service-pending"}>{apiReady ? "Online" : api.status}</strong></div>
          <div className="service-row"><span><i className={`service-indicator ${databaseReady ? "" : "pending"}`} /> PostgreSQL</span><strong className={databaseReady ? "service-ok" : "service-pending"}>{databaseReady ? "Healthy" : "A validar"}</strong></div>
          <div className="service-row"><span><i className={`service-indicator ${redisReady ? "" : "pending"}`} /> Redis</span><strong className={redisReady ? "service-ok" : "service-pending"}>{redisReady ? "Healthy" : "A validar"}</strong></div>
        </article>
        <article className="panel principle-panel">
          <p className="eyebrow">REGRA FUNDAMENTAL</p>
          <h2>Zero Curriculum Gaps</h2>
          <p>Todos os tópicos terão profundidade equivalente no Learning Center e no Internship Center. Fundamentos como discos, partições, filesystems, mount, DNS e permissões terão laboratórios e responsabilidades empresariais próprias.</p>
          <Link href="/internship" className="text-link">Ver modelo de estágio <span>→</span></Link>
        </article>
      </section>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/auth/auth-provider";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type ModuleProgress = {
  module_code: string; source_module_code: string | null; title: string; track_code: string | null;
  estimated_hours: number | null; lessons_total: number; lessons_completed: number;
  labs_total: number; labs_validated: number; lab_attempts: number;
  assessments_total: number; assessment_attempts: number; assessment_reviews_pending: number;
  competencies_total: number; competencies_mastered: number; competencies_in_progress: number;
};
type Summary = {
  lessons_total: number; lessons_completed: number; labs_total: number; labs_validated: number;
  lab_attempts: number; assessments_total: number; assessment_attempts: number;
  assessment_reviews_pending: number; assessments_passed: number; competencies_total: number;
  competencies_mastered: number; competencies_in_progress: number; evidence_submitted: number; evidence_accepted: number;
};
type ProgressData = { user: { display_name: string; email: string }; summary: Summary; modules: ModuleProgress[] };

function percent(done: number, total: number) { return total > 0 ? Math.round((done / total) * 100) : 0; }

export default function ProgressPage() {
  const { user } = useAuth();
  const [data, setData] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE}/learning/me/progress`, { credentials: "include", cache: "no-store" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Falha ao carregar progresso (${response.status}).`);
      setData(payload as ProgressData);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível carregar o progresso."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  return <div className="progress-page">
    <div className="page-heading"><div><p className="eyebrow">LEARNING CENTER / PERSONAL RECORD</p><h1>O meu progresso</h1><p className="page-description">Histórico associado à tua conta. Concluir uma aula é uma declaração de estudo; dominar uma competência exige revisão e evidência verificável.</p></div><span className="status-pill planned">M2 · Learning Progress</span></div>
    {error ? <div className="form-alert error" role="alert">{error}</div> : null}
    {loading ? <section className="panel progress-empty"><p>A carregar o teu histórico…</p></section> : null}
    {!loading && data ? <>
      <section className="progress-welcome panel"><div><p className="panel-kicker">PERFIL DE APRENDIZAGEM</p><h2>{data.user.display_name}</h2><p>{data.user.email}</p></div><button className="button-secondary" onClick={() => void load()}>Atualizar</button></section>
      <section className="progress-summary-grid">
        <article className="panel progress-metric"><span>Aulas concluídas</span><strong>{data.summary.lessons_completed}<small> / {data.summary.lessons_total}</small></strong><div className="progress-track"><i style={{ width: `${percent(data.summary.lessons_completed, data.summary.lessons_total)}%` }} /></div></article>
        <article className="panel progress-metric"><span>Laboratórios validados</span><strong>{data.summary.labs_validated}<small> / {data.summary.labs_total}</small></strong><div className="progress-track"><i style={{ width: `${percent(data.summary.labs_validated, data.summary.labs_total)}%` }} /></div></article>
        <article className="panel progress-metric"><span>Avaliações aprovadas</span><strong>{data.summary.assessments_passed}<small> · {data.summary.assessment_attempts} tentativas</small></strong><div className="progress-track"><i style={{ width: `${percent(data.summary.assessments_passed, data.summary.assessments_total)}%` }} /></div></article>
        <article className="panel progress-metric"><span>Competências dominadas</span><strong>{data.summary.competencies_mastered}<small> / {data.summary.competencies_total}</small></strong><div className="progress-track"><i style={{ width: `${percent(data.summary.competencies_mastered, data.summary.competencies_total)}%` }} /></div></article>
      </section>
      <section className="progress-secondary-grid">
        <article className="panel progress-secondary"><span>Submissões à espera de revisão</span><strong>{data.summary.assessment_reviews_pending}</strong><small>Avaliações pendentes</small></article>
        <article className="panel progress-secondary"><span>Tentativas de laboratório</span><strong>{data.summary.lab_attempts}</strong><small>{data.summary.labs_validated} laboratório(s) validados</small></article>
        <article className="panel progress-secondary"><span>Evidências aceites</span><strong>{data.summary.evidence_accepted}<small> / {data.summary.evidence_submitted}</small></strong><small>Portfólio técnico</small></article>
      </section>
      <section className="panel progress-modules-panel"><div className="section-heading compact"><div><p className="eyebrow">CURRÍCULO CANÓNICO</p><h2>Progresso por módulo</h2></div><span className="subtle-label">{data.modules.length} módulos</span></div>
        {data.modules.map((module) => <article className="progress-module-row" key={module.module_code}><div className="progress-module-title"><div><small>{module.track_code ?? "CURRÍCULO"} · {module.source_module_code ?? module.module_code}</small><strong>{module.title}</strong></div><Link href={`/learning/${encodeURIComponent(module.module_code)}`} className="text-link">Abrir módulo →</Link></div><div className="progress-module-metrics"><span>Aulas {module.lessons_completed}/{module.lessons_total}</span><span>Labs validados {module.labs_validated}/{module.labs_total}</span><span>Competências {module.competencies_mastered}/{module.competencies_total}</span><span>Avaliações {module.assessment_attempts}</span></div><div className="progress-track"><i style={{ width: `${percent(module.lessons_completed, module.lessons_total)}%` }} /></div></article>)}
      </section>
    </> : null}
    {!loading && !data && !error ? <section className="panel progress-empty">Ainda não existe histórico associado à tua conta.</section> : null}
  </div>;
}

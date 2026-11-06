"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/auth/auth-provider";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type LabReviewItem = { id: string; status: string; lab_code: string; lab_title: string; learner_name: string; learner_email: string; learner_notes: string | null; submission: Record<string, unknown>; submitted_at: string | null };
type AssessmentReviewItem = { id: string; status: string; assessment_code: string; assessment_title: string; total_points: number; mastery_threshold: number; questions: { id: string; prompt: string; points: number }[]; learner_name: string; learner_email: string; answers: Record<string, unknown>; submitted_at: string };
type EvidenceReviewItem = { id: string; title: string; evidence_type: string; summary: string | null; artifact_uri: string | null; competency_code: string; competency_title: string; learner_name: string; learner_email: string; created_at: string };
type CompetencyReviewItem = { competency_id: string; competency_code: string; competency_title: string; learner_user_id: string; learner_name: string; learner_email: string; self_assessment_notes: string | null; updated_at: string };
type Queue = { lab_attempts: LabReviewItem[]; assessment_attempts: AssessmentReviewItem[]; evidence: EvidenceReviewItem[]; competency_reviews: CompetencyReviewItem[] };

export default function ReviewsPage() {
  const { user, csrfToken } = useAuth();
  const [queue, setQueue] = useState<Queue | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [labOutcomes, setLabOutcomes] = useState<Record<string, string>>({});
  const [labNotes, setLabNotes] = useState<Record<string, string>>({});
  const [scores, setScores] = useState<Record<string, string>>({});
  const [assessmentFeedback, setAssessmentFeedback] = useState<Record<string, string>>({});
  const [evidenceOutcomes, setEvidenceOutcomes] = useState<Record<string, string>>({});
  const [evidenceNotes, setEvidenceNotes] = useState<Record<string, string>>({});
  const [competencyOutcomes, setCompetencyOutcomes] = useState<Record<string, string>>({});
  const [competencyScores, setCompetencyScores] = useState<Record<string, string>>({});
  const [competencyNotes, setCompetencyNotes] = useState<Record<string, string>>({});

  const permitted = Boolean(user?.permissions.includes("assessments:review") || user?.permissions.includes("labs:review") || user?.permissions.includes("portfolio:review"));
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE}/learning/review-queue`, { credentials: "include", cache: "no-store" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Falha ao carregar fila (${response.status}).`);
      setQueue(payload as Queue);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível carregar a fila de revisão."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { if (permitted) void load(); else setLoading(false); }, [load, permitted]);

  async function mutate(path: string, body: unknown) {
    if (!csrfToken) throw new Error("Token CSRF indisponível. Atualiza a sessão.");
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Revisão recusada (${response.status}).`);
    return payload;
  }

  async function action(key: string, task: () => Promise<void>) {
    setBusy(key); setError(null); setSuccess(null);
    try { await task(); setSuccess("Revisão registada na auditoria."); await load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "A revisão falhou."); }
    finally { setBusy(null); }
  }

  function reviewLab(event: FormEvent<HTMLFormElement>, item: LabReviewItem) {
    event.preventDefault();
    return action(`lab-${item.id}`, async () => {
      const outcome = labOutcomes[item.id] ?? "validated";
      await mutate(`/learning/lab-attempts/${item.id}/review`, {
        outcome, validation_report: { reviewer_note: labNotes[item.id] ?? "", reviewed_via: "review_center" },
      });
    });
  }

  function reviewAssessment(event: FormEvent<HTMLFormElement>, item: AssessmentReviewItem) {
    event.preventDefault();
    return action(`assessment-${item.id}`, async () => {
      const raw = scores[item.id];
      if (raw === undefined || raw.trim() === "") throw new Error("Indica a pontuação atribuída.");
      const score = Number(raw);
      if (!Number.isFinite(score) || score < 0 || score > item.total_points) throw new Error(`A nota deve estar entre 0 e ${item.total_points}.`);
      await mutate(`/learning/assessment-attempts/${item.id}/review`, {
        score, feedback: { reviewer_note: assessmentFeedback[item.id] ?? "", reviewed_via: "review_center" },
      });
    });
  }

  function reviewEvidence(event: FormEvent<HTMLFormElement>, item: EvidenceReviewItem) {
    event.preventDefault();
    return action(`evidence-${item.id}`, async () => {
      await mutate(`/learning/evidence/${item.id}/review`, {
        review_status: evidenceOutcomes[item.id] ?? "accepted",
        review_note: evidenceNotes[item.id] ?? "Revisão técnica registada.",
      });
    });
  }

  function reviewCompetency(event: FormEvent<HTMLFormElement>, item: CompetencyReviewItem) {
    event.preventDefault();
    return action(`competency-${item.competency_id}-${item.learner_user_id}`, async () => {
      const outcome = competencyOutcomes[item.competency_id] ?? "demonstrated";
      const rawScore = competencyScores[item.competency_id];
      const masteryScore = rawScore !== undefined && rawScore.trim() !== "" ? Number(rawScore) : null;
      if (outcome === "mastered" && (masteryScore === null || !Number.isFinite(masteryScore) || masteryScore < 0 || masteryScore > 100)) {
        throw new Error("Para validar domínio, indica uma nota entre 0 e 100.");
      }
      await mutate(`/learning/competencies/${item.competency_id}/review`, {
        learner_user_id: item.learner_user_id,
        status: outcome,
        mastery_score: masteryScore,
        notes: competencyNotes[item.competency_id] ?? "Revisão técnica registada.",
      });
    });
  }

  if (!permitted) return <section className="panel admin-denied"><p className="eyebrow">QUALITY REVIEW / ACCESS CONTROL</p><h1>Acesso restrito</h1><p>A tua conta não possui permissões de revisão.</p></section>;

  return <div className="review-page">
    <div className="page-heading"><div><p className="eyebrow">QUALITY GOVERNANCE / REVIEW WORKFLOW</p><h1>Fila de revisão técnica</h1><p className="page-description">Revê submissões de laboratórios, avaliações e evidências. Cada decisão fica associada ao revisor e ao registo de auditoria.</p></div><span className="status-pill planned">M2 · Reviewer Workspace</span></div>
    {error ? <div className="form-alert error" role="alert">{error}</div> : null}
    {success ? <div className="form-alert success" role="status">{success}</div> : null}
    <div className="section-heading compact"><div><p className="eyebrow">PENDING WORK</p><h2>Submissões pendentes</h2></div><button className="button-secondary" type="button" onClick={() => void load()} disabled={loading}>Atualizar fila</button></div>
    {loading ? <section className="panel progress-empty">A carregar fila…</section> : null}
    {queue ? <>
      <section className="review-section"><div className="review-section-heading"><h2>Laboratórios</h2><span>{queue.lab_attempts.length} pendente(s)</span></div>{queue.lab_attempts.map((item) => <article className="panel review-card" key={item.id}><div className="review-card-heading"><div><p className="panel-kicker">{item.lab_code}</p><h3>{item.lab_title}</h3><small>{item.learner_name} · {item.learner_email} · {item.submitted_at ? new Date(item.submitted_at).toLocaleString() : "Data não registada"}</small></div><span className="status-pill planned">{item.status}</span></div><p>{item.learner_notes || "Sem notas do estudante."}</p><details><summary>Consultar submissão técnica</summary><pre className="lesson-code"><code>{JSON.stringify(item.submission, null, 2)}</code></pre></details><form className="review-form" onSubmit={(event) => void reviewLab(event, item)}><label>Decisão<select value={labOutcomes[item.id] ?? "validated"} onChange={(event) => setLabOutcomes((current) => ({ ...current, [item.id]: event.target.value }))}><option value="validated">Validar</option><option value="returned">Devolver para correção</option><option value="failed">Não validar</option></select></label><label>Nota técnica<textarea rows={2} value={labNotes[item.id] ?? ""} onChange={(event) => setLabNotes((current) => ({ ...current, [item.id]: event.target.value }))} /></label><button className="button-primary" disabled={busy !== null || !csrfToken}>Registar revisão</button></form></article>)}</section>
      <section className="review-section"><div className="review-section-heading"><h2>Avaliações</h2><span>{queue.assessment_attempts.length} pendente(s)</span></div>{queue.assessment_attempts.map((item) => <article className="panel review-card" key={item.id}><div className="review-card-heading"><div><p className="panel-kicker">{item.assessment_code}</p><h3>{item.assessment_title}</h3><small>{item.learner_name} · {item.learner_email} · {new Date(item.submitted_at).toLocaleString()}</small></div><span className="status-pill planned">{item.status}</span></div><div className="review-answers">{Object.entries(item.answers).map(([questionId, answer]) => <div key={questionId}><strong>{questionId}</strong><p>{String(answer)}</p></div>)}</div><form className="review-form" onSubmit={(event) => void reviewAssessment(event, item)}><label>Nota (0–{item.total_points})<input type="number" min="0" max={item.total_points} step="0.5" value={scores[item.id] ?? ""} onChange={(event) => setScores((current) => ({ ...current, [item.id]: event.target.value }))} required /></label><label>Feedback técnico<textarea rows={3} value={assessmentFeedback[item.id] ?? ""} onChange={(event) => setAssessmentFeedback((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Pontos fortes, lacunas, erros e reforço recomendado…" /></label><button className="button-primary" disabled={busy !== null || !csrfToken}>Corrigir avaliação</button><small>Critério de aprovação configurado: {item.mastery_threshold}%.</small></form></article>)}</section>
      <section className="review-section"><div className="review-section-heading"><h2>Evidências</h2><span>{queue.evidence.length} pendente(s)</span></div>{queue.evidence.map((item) => <article className="panel review-card" key={item.id}><div className="review-card-heading"><div><p className="panel-kicker">{item.competency_code} · {item.evidence_type}</p><h3>{item.title}</h3><small>{item.competency_title} · {item.learner_name} · {item.learner_email}</small></div><span className="status-pill planned">Pendente</span></div><p>{item.summary}</p>{item.artifact_uri ? <p className="subtle-label">Referência: {item.artifact_uri}</p> : null}<form className="review-form" onSubmit={(event) => void reviewEvidence(event, item)}><label>Decisão<select value={evidenceOutcomes[item.id] ?? "accepted"} onChange={(event) => setEvidenceOutcomes((current) => ({ ...current, [item.id]: event.target.value }))}><option value="accepted">Aceitar</option><option value="needs_changes">Pedir alterações</option><option value="rejected">Rejeitar</option></select></label><label>Justificação<textarea rows={2} minLength={5} value={evidenceNotes[item.id] ?? ""} onChange={(event) => setEvidenceNotes((current) => ({ ...current, [item.id]: event.target.value }))} required /></label><button className="button-primary" disabled={busy !== null || !csrfToken}>Registar decisão</button></form></article>)}</section>
      <section className="review-section"><div className="review-section-heading"><h2>Competências submetidas para validação</h2><span>{queue.competency_reviews.length} pendente(s)</span></div>{queue.competency_reviews.map((item) => <article className="panel review-card" key={`${item.competency_id}-${item.learner_user_id}`}><div className="review-card-heading"><div><p className="panel-kicker">{item.competency_code}</p><h3>{item.competency_title}</h3><small>{item.learner_name} · {item.learner_email} · {new Date(item.updated_at).toLocaleString()}</small></div><span className="status-pill planned">Self-assessed</span></div><p>{item.self_assessment_notes || "O estudante não acrescentou notas."}</p><form className="review-form" onSubmit={(event) => void reviewCompetency(event, item)}><label>Resultado da revisão<select value={competencyOutcomes[item.competency_id] ?? "demonstrated"} onChange={(event) => setCompetencyOutcomes((current) => ({ ...current, [item.competency_id]: event.target.value }))}><option value="demonstrated">Demonstrado</option><option value="mastered">Dominado</option><option value="requires_reinforcement">Necessita reforço</option></select></label><label>Nota de domínio (obrigatória se escolheres “Dominado”)<input type="number" min="0" max="100" step="0.5" value={competencyScores[item.competency_id] ?? ""} onChange={(event) => setCompetencyScores((current) => ({ ...current, [item.competency_id]: event.target.value }))} /></label><label>Justificação técnica<textarea rows={2} minLength={5} value={competencyNotes[item.competency_id] ?? ""} onChange={(event) => setCompetencyNotes((current) => ({ ...current, [item.competency_id]: event.target.value }))} required /></label><button className="button-primary" disabled={busy !== null || !csrfToken}>Validar competência</button></form></article>)}</section>
      {queue.lab_attempts.length + queue.assessment_attempts.length + queue.evidence.length + queue.competency_reviews.length === 0 ? <section className="panel progress-empty">Não existem submissões pendentes para revisão.</section> : null}
    </> : null}
  </div>;
}

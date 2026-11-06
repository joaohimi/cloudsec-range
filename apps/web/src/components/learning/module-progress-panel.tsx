"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth/auth-provider";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type LessonItem = { id: string; code: string; title: string; sequence: number; progress_status: string; completion_percent: number; time_spent_seconds: number };
type LabAttempt = { id: string; status: string; started_at: string; submitted_at: string | null; reviewed_at: string | null; learner_notes: string | null; validation_report: Record<string, unknown> };
type LabItem = { id: string; code: string; title: string; status: string; attempt_count: number; latest_attempt: LabAttempt | null; attempts: LabAttempt[] };
type AssessmentAttempt = { id: string; review_status: string; score: number | null; passed: boolean | null; submitted_at: string; feedback: Record<string, unknown> };
type AssessmentItem = { id: string; code: string; title: string; status: string; total_points: number; mastery_threshold: number; attempt_count: number; best_score: number | null; attempts: AssessmentAttempt[] };
type CompetencyItem = { id: string; code: string; title: string; description: string; status: string; mastery_score: number | null; self_assessment_notes: string | null; review_notes: string | null };
type EvidenceItem = { id: string; competency_id: string; evidence_type: string; title: string; review_status: string; summary: string; created_at: string };
type ModuleProgress = { module: { code: string; title: string; estimated_hours: number | null }; lessons: LessonItem[]; labs: LabItem[]; assessments: AssessmentItem[]; competencies: CompetencyItem[]; evidence: EvidenceItem[] };
type Question = { id: string; prompt: string; points: number };
type AssessmentProp = { id: string; code: string; title: string; rubric?: { questions?: Question[] } };
type Props = { moduleCode: string; assessments: AssessmentProp[] };

function statusLabel(value: string) {
  const labels: Record<string, string> = {
    not_started: "Não iniciada", in_progress: "Em curso", completed: "Concluída",
    started: "Iniciada", submitted: "Submetida", in_review: "Em revisão",
    validated: "Validada", failed: "Não validada", returned: "Devolvida",
    reviewed: "Corrigida", mastered: "Dominada", self_assessed: "Autoavaliação submetida",
    demonstrated: "Demonstrada", requires_reinforcement: "Precisa de reforço", pending: "Pendente",
    accepted: "Aceite", rejected: "Rejeitada", needs_changes: "Requer alterações",
  };
  return labels[value] ?? value;
}

export function ModuleProgressPanel({ moduleCode, assessments }: Props) {
  const { csrfToken } = useAuth();
  const [data, setData] = useState<ModuleProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [labNotes, setLabNotes] = useState<Record<string, string>>({});
  const [answers, setAnswers] = useState<Record<string, Record<string, string>>>({});
  const [competencyNotes, setCompetencyNotes] = useState<Record<string, string>>({});
  const [evidenceCompetency, setEvidenceCompetency] = useState("");
  const [evidenceSource, setEvidenceSource] = useState("");
  const [evidenceTitle, setEvidenceTitle] = useState("");
  const [evidenceSummary, setEvidenceSummary] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE}/learning/modules/${encodeURIComponent(moduleCode)}/progress`, { credentials: "include", cache: "no-store" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Erro ao consultar progresso (${response.status}).`);
      setData(payload as ModuleProgress);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível carregar o progresso."); }
    finally { setLoading(false); }
  }, [moduleCode]);
  useEffect(() => { void load(); }, [load]);

  async function mutate(path: string, method: string, body?: unknown) {
    if (!csrfToken) throw new Error("Token CSRF indisponível. Atualiza a sessão.");
    const response = await fetch(`${API_BASE}${path}`, {
      method, credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Operação recusada (${response.status}).`);
    return payload;
  }

  async function runAction(key: string, task: () => Promise<void>) {
    setBusy(key); setError(null); setSuccess(null);
    try { await task(); await load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "A operação falhou."); }
    finally { setBusy(null); }
  }

  function updateLesson(lesson: LessonItem, nextStatus: "in_progress" | "completed") {
    return runAction(`lesson-${lesson.id}`, async () => {
      await mutate(`/learning/lessons/${lesson.id}/progress`, "PUT", {
        status: nextStatus,
        completion_percent: nextStatus === "completed" ? 100 : lesson.completion_percent,
        time_spent_seconds: lesson.time_spent_seconds,
        last_position: {},
      });
      setSuccess(nextStatus === "completed" ? "Aula registada como concluída." : "Início da aula registado.");
    });
  }

  function startLab(lab: LabItem) {
    return runAction(`lab-${lab.id}`, async () => {
      await mutate(`/learning/labs/${lab.id}/attempts`, "POST");
      setSuccess("Tentativa de laboratório iniciada. Executa o laboratório no teu ambiente e depois submete o relatório.");
    });
  }

  function submitLab(labId: string, attempt: LabAttempt) {
    return runAction(`lab-submit-${attempt.id}`, async () => {
      await mutate(`/learning/lab-attempts/${attempt.id}/submit`, "PATCH", {
        learner_notes: labNotes[attempt.id] ?? "Execução concluída conforme os passos do laboratório. Consulte as evidências anexadas à submissão.",
        submission: { submitted_from: "learning_center", module_code: moduleCode },
      });
      setSuccess("Relatório do laboratório submetido para revisão técnica.");
    });
  }

  function submitAssessment(event: FormEvent<HTMLFormElement>, assessment: AssessmentProp) {
    event.preventDefault();
    const values = answers[assessment.id] ?? {};
    return runAction(`assessment-${assessment.id}`, async () => {
      if (!Object.keys(values).length || Object.values(values).every((value) => !value.trim())) throw new Error("Responde a pelo menos uma pergunta antes de submeter.");
      await mutate(`/learning/assessments/${assessment.id}/attempts`, "POST", { answers: values });
      setAnswers((current) => ({ ...current, [assessment.id]: {} }));
      setSuccess("Avaliação submetida. A nota será atribuída após revisão técnica; não existe classificação automática nesta versão.");
    });
  }

  function selfAssess(competency: CompetencyItem) {
    return runAction(`competency-${competency.id}`, async () => {
      const notes = competencyNotes[competency.id] ?? ""
      await mutate(`/learning/competencies/${competency.id}/self-assessment`, "PUT", { status: "self_assessed", notes });
      setSuccess("Autoavaliação submetida. A competência continua à espera de validação técnica.");
    });
  }

  const evidenceSources = useMemo(() => {
    if (!data) return [] as { value: string; label: string }[];
    const lessonSources = data.lessons.filter((item) => item.progress_status === "completed").map((item) => ({ value: `lesson:${item.id}`, label: `Aula concluída · ${item.title}` }));
    const labSources = data.labs.flatMap((lab) => lab.attempts.filter((attempt) => ["submitted", "validated"].includes(attempt.status)).map((attempt) => ({ value: `lab:${lab.id}`, label: `Laboratório submetido · ${lab.title} (${statusLabel(attempt.status)})` })));
    const assessmentSources = data.assessments.flatMap((assessment) => assessment.attempts.map((attempt) => ({ value: `assessment:${attempt.id}`, label: `Avaliação · ${assessment.title} (${statusLabel(attempt.review_status)})` })));
    return [...lessonSources, ...labSources, ...assessmentSources];
  }, [data]);

  function submitEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    return runAction("evidence", async () => {
      if (!evidenceCompetency || !evidenceSource) throw new Error("Seleciona uma competência e uma origem para a evidência.");
      const [sourceType, sourceId] = evidenceSource.split(":");
      const body: Record<string, unknown> = {
        competency_id: evidenceCompetency, evidence_type: "learning_artifact",
        title: evidenceTitle, summary: evidenceSummary,
      };
      if (sourceType === "lesson") body.lesson_id = sourceId;
      if (sourceType === "lab") body.lab_id = sourceId;
      if (sourceType === "assessment") body.assessment_attempt_id = sourceId;
      await mutate("/learning/evidence", "POST", body);
      setEvidenceTitle(""); setEvidenceSummary("");
      setSuccess("Evidência registada e enviada para revisão.");
    });
  }

  return <section className="module-section module-progress-section">
    <div className="module-section-heading"><div><p className="panel-kicker">M2 · LEARNING PROGRESS</p><h2>O teu trabalho nesta unidade</h2></div><button type="button" className="text-button" onClick={() => void load()} disabled={loading}>Atualizar</button></div>
    <p className="progress-explainer">O progresso fica ligado à tua conta. A conclusão de uma aula é registada como atividade do estudante; laboratórios e avaliações submetidos aguardam revisão; competências dominadas nunca são autoatribuídas.</p>
    {error ? <div className="form-alert error" role="alert">{error}</div> : null}
    {success ? <div className="form-alert success" role="status">{success}</div> : null}
    {loading ? <article className="panel progress-empty">A carregar progresso da unidade…</article> : null}
    {data ? <>
      <div className="module-progress-grid">
        <article className="panel module-progress-card"><p className="panel-kicker">AULAS</p><h3>{data.lessons.filter((item) => item.progress_status === "completed").length} / {data.lessons.length}</h3><small>Concluídas</small><div className="module-progress-list">{data.lessons.map((lesson) => <div className="module-progress-item" key={lesson.id}><div><strong>{lesson.sequence}. {lesson.title}</strong><small>{statusLabel(lesson.progress_status)}</small></div><div className="inline-actions">{lesson.progress_status === "not_started" ? <button type="button" className="text-button" disabled={busy !== null} onClick={() => void updateLesson(lesson, "in_progress")}>Iniciar</button> : null}{lesson.progress_status !== "completed" ? <button type="button" className="text-button positive" disabled={busy !== null} onClick={() => void updateLesson(lesson, "completed")}>Concluir</button> : <span className="status-pill success">Concluída</span>}</div></div>)}</div></article>
        <article className="panel module-progress-card"><p className="panel-kicker">LABORATÓRIOS</p><h3>{data.labs.filter((item) => item.attempts.some((attempt) => attempt.status === "validated")).length} / {data.labs.length}</h3><small>Validados por revisão</small><div className="module-progress-list">{data.labs.map((lab) => <div className="module-progress-item stacked" key={lab.id}><div><strong>{lab.title}</strong><small>{lab.attempt_count} tentativa(s) · {lab.latest_attempt ? statusLabel(lab.latest_attempt.status) : "Ainda não iniciado"}</small></div>{lab.attempts.filter((attempt) => ["started", "returned"].includes(attempt.status)).map((attempt) => <div className="lab-submit-inline" key={attempt.id}><textarea value={labNotes[attempt.id] ?? ""} onChange={(event) => setLabNotes((current) => ({ ...current, [attempt.id]: event.target.value }))} rows={2} placeholder="Regista o que executaste, resultados observados e eventuais erros…" /><button type="button" className="text-button positive" disabled={busy !== null} onClick={() => void submitLab(lab.id, attempt)}>Submeter para revisão</button></div>)}<div className="inline-actions">{!lab.attempts.some((attempt) => ["started", "submitted", "in_review"].includes(attempt.status)) ? <button type="button" className="text-button" disabled={busy !== null} onClick={() => void startLab(lab)}>Iniciar tentativa</button> : null}</div></div>)}</div></article>
      </div>
      <article className="panel module-progress-card module-assessments-card"><div className="section-heading compact"><div><p className="panel-kicker">AVALIAÇÕES</p><h3>Submeter trabalho para correção</h3></div></div>{assessments.map((assessment) => { const progressAssessment = data.assessments.find((item) => item.id === assessment.id); return <form className="assessment-submit-form" key={assessment.id} onSubmit={(event) => void submitAssessment(event, assessment)}><div className="module-progress-item"><div><strong>{assessment.title}</strong><small>{progressAssessment?.attempt_count ?? 0} tentativa(s) · melhor nota revista: {progressAssessment?.best_score ?? "Ainda sem nota"}</small></div><button className="text-button positive" type="submit" disabled={busy !== null}>Submeter avaliação</button></div>{assessment.rubric?.questions?.map((question) => <label className="assessment-answer" key={question.id}><span>{question.id} · {question.points} ponto(s) · {question.prompt}</span><textarea rows={3} value={answers[assessment.id]?.[question.id] ?? ""} onChange={(event) => setAnswers((current) => ({ ...current, [assessment.id]: { ...(current[assessment.id] ?? {}), [question.id]: event.target.value } }))} placeholder="Escreve a tua resposta…" /></label>)}</form>; })}</article>
      <article className="panel module-progress-card"><div className="section-heading compact"><div><p className="panel-kicker">COMPETÊNCIAS</p><h3>Autoavaliação e domínio validado</h3></div></div>{data.competencies.map((competency) => <div className="competency-progress-row" key={competency.id}><div><strong>{competency.code} · {competency.title}</strong><small>{statusLabel(competency.status)}{competency.mastery_score !== null ? ` · ${competency.mastery_score}/100` : ""}</small></div>{!(["mastered", "demonstrated"].includes(competency.status)) ? <div className="competency-self-assessment"><textarea rows={2} value={competencyNotes[competency.id] ?? competency.self_assessment_notes ?? ""} onChange={(event) => setCompetencyNotes((current) => ({ ...current, [competency.id]: event.target.value }))} placeholder="Descreve o que consegues explicar, aplicar e demonstrar…" /><button type="button" className="text-button" disabled={busy !== null || (competencyNotes[competency.id] ?? competency.self_assessment_notes ?? "").trim().length < 10} onClick={() => void selfAssess(competency)}>Submeter autoavaliação</button></div> : null}</div>)}</article>
      <article className="panel module-progress-card"><div className="section-heading compact"><div><p className="panel-kicker">PORTFÓLIO / EVIDÊNCIAS</p><h3>Registar evidência</h3></div></div><form className="evidence-submit-form" onSubmit={(event) => void submitEvidence(event)}><label>Competência<select value={evidenceCompetency} onChange={(event) => setEvidenceCompetency(event.target.value)} required><option value="">Selecionar competência</option>{data.competencies.map((item) => <option value={item.id} key={item.id}>{item.code} · {item.title}</option>)}</select></label><label>Origem<select value={evidenceSource} onChange={(event) => setEvidenceSource(event.target.value)} required><option value="">Selecionar trabalho associado</option>{evidenceSources.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select></label><label>Título da evidência<input value={evidenceTitle} onChange={(event) => setEvidenceTitle(event.target.value)} minLength={3} maxLength={240} required /></label><label>Resumo e contexto<textarea rows={3} value={evidenceSummary} onChange={(event) => setEvidenceSummary(event.target.value)} minLength={10} required placeholder="Explica o que a evidência demonstra e como foi produzida…" /></label><button className="button-primary" type="submit" disabled={busy !== null || !csrfToken}>Registar evidência</button></form><div className="evidence-history">{data.evidence.map((item) => <div className="module-progress-item" key={item.id}><div><strong>{item.title}</strong><small>{item.evidence_type} · {new Date(item.created_at).toLocaleString()}</small></div><span className="status-pill planned">{statusLabel(item.review_status)}</span></div>)}{data.evidence.length === 0 ? <p className="empty-state">Ainda não existem evidências submetidas nesta unidade.</p> : null}</div></article>
    </> : null}
  </section>;
}

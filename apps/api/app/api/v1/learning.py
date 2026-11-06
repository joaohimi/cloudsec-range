from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.auth_dependencies import AuthContext, require_csrf, require_permission
from app.api.v1.learning_schemas import (
    AssessmentAttemptCreate, AssessmentAttemptReview, CompetencyReview,
    CompetencySelfAssessment, EvidenceCreate, EvidenceReview, LabAttemptReview,
    LabAttemptSubmit, LessonProgressUpdate,
)
from app.db.session import get_db
from app.models.auth import AuditEvent, User
from app.models.curriculum import (
    Assessment, AssessmentAttempt, Competency, CompetencyProgress, CurriculumModule,
    CurriculumTrack, Evidence, Lab, Lesson, LearningResource,
)
from app.models.internship import InternshipTicket
from app.models.learning import LabAttempt, LessonProgress
from app.models.curriculum import assessment_competencies, lab_competencies, lesson_competencies

router = APIRouter()


def _audit(db: Session, request: Request, actor_id: UUID, action: str, target_type: str, target_id: str, details: dict | None = None) -> None:
    db.add(AuditEvent(
        actor_user_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        outcome="success",
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500] or None,
        details=details or {},
    ))


def _module_or_404(db: Session, module_code: str) -> CurriculumModule:
    module = db.scalar(select(CurriculumModule).where(CurriculumModule.code == module_code))
    if module is None:
        raise HTTPException(status_code=404, detail="Módulo curricular não encontrado.")
    return module


def _serialize_lesson_progress(lesson: Lesson, progress: LessonProgress | None) -> dict:
    return {
        "id": str(lesson.id), "code": lesson.code, "title": lesson.title,
        "sequence": lesson.sequence,
        "content_status": lesson.status,
        "progress_status": progress.status if progress else "not_started",
        "completion_percent": progress.completion_percent if progress else 0,
        "time_spent_seconds": progress.time_spent_seconds if progress else 0,
        "started_at": progress.started_at.isoformat() if progress else None,
        "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
    }


def _serialize_lab(lab: Lab, attempts: list[LabAttempt]) -> dict:
    ordered = sorted(attempts, key=lambda item: item.created_at, reverse=True)
    latest = ordered[0] if ordered else None
    return {
        "id": str(lab.id), "code": lab.code, "title": lab.title,
        "status": lab.status, "attempt_count": len(ordered),
        "latest_attempt": {
            "id": str(latest.id), "status": latest.status,
            "started_at": latest.started_at.isoformat(),
            "submitted_at": latest.submitted_at.isoformat() if latest.submitted_at else None,
            "reviewed_at": latest.reviewed_at.isoformat() if latest.reviewed_at else None,
        } if latest else None,
        "attempts": [{
            "id": str(item.id), "status": item.status,
            "started_at": item.started_at.isoformat(),
            "submitted_at": item.submitted_at.isoformat() if item.submitted_at else None,
            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
            "learner_notes": item.learner_notes,
            "validation_report": item.validation_report,
        } for item in ordered],
    }


def _serialize_assessment(assessment: Assessment, attempts: list[AssessmentAttempt]) -> dict:
    ordered = sorted(attempts, key=lambda item: item.submitted_at, reverse=True)
    reviewed = [item for item in ordered if item.review_status == "reviewed"]
    return {
        "id": str(assessment.id), "code": assessment.code, "title": assessment.title,
        "status": assessment.status, "total_points": assessment.total_points,
        "mastery_threshold": assessment.mastery_threshold,
        "attempt_count": len(ordered),
        "best_score": max((item.score for item in reviewed), default=None),
        "attempts": [{
            "id": str(item.id), "review_status": item.review_status,
            "score": item.score if item.review_status == "reviewed" else None,
            "passed": item.passed if item.review_status == "reviewed" else None,
            "submitted_at": item.submitted_at.isoformat(),
            "feedback": item.feedback if item.review_status == "reviewed" else {},
        } for item in ordered],
    }


def _serialize_competency(competency: Competency, progress: CompetencyProgress | None) -> dict:
    return {
        "id": str(competency.id), "code": competency.code, "title": competency.title,
        "description": competency.description,
        "status": progress.status if progress else "not_started",
        "mastery_score": progress.mastery_score if progress else None,
        "self_assessment_notes": progress.self_assessment_notes if progress else None,
        "review_notes": progress.notes if progress else None,
        "last_assessed_at": progress.last_assessed_at.isoformat() if progress and progress.last_assessed_at else None,
    }


@router.get("/me/progress", dependencies=[Depends(require_permission("learning:read"))])
def get_my_progress(
    context: AuthContext = Depends(require_permission("learning:read")),
    db: Session = Depends(get_db),
) -> dict:
    modules = list(db.scalars(
        select(CurriculumModule)
        .options(selectinload(CurriculumModule.track))
        .join(CurriculumModule.track)
        .order_by(CurriculumTrack.position, CurriculumModule.position)
    ))
    module_ids = [item.id for item in modules]
    if not module_ids:
        return {"user": {"id": str(context.user.id), "display_name": context.user.display_name}, "summary": {}, "modules": []}

    lessons = list(db.scalars(select(Lesson).where(Lesson.module_id.in_(module_ids))))
    lesson_ids = [item.id for item in lessons]
    lesson_progress = list(db.scalars(select(LessonProgress).where(
        LessonProgress.user_id == context.user.id,
        LessonProgress.lesson_id.in_(lesson_ids or [UUID(int=0)]),
    )))
    labs = list(db.scalars(select(Lab).where(Lab.module_id.in_(module_ids))))
    lab_ids = [item.id for item in labs]
    lab_attempts = list(db.scalars(select(LabAttempt).where(
        LabAttempt.user_id == context.user.id,
        LabAttempt.lab_id.in_(lab_ids or [UUID(int=0)]),
    )))
    assessments = list(db.scalars(select(Assessment).where(Assessment.module_id.in_(module_ids))))
    assessment_ids = [item.id for item in assessments]
    assessment_attempts = list(db.scalars(select(AssessmentAttempt).where(
        AssessmentAttempt.user_id == context.user.id,
        AssessmentAttempt.assessment_id.in_(assessment_ids or [UUID(int=0)]),
    )))
    competencies = list(db.scalars(select(Competency).where(Competency.module_id.in_(module_ids))))
    competency_ids = [item.id for item in competencies]
    competency_progress = list(db.scalars(select(CompetencyProgress).where(
        CompetencyProgress.user_id == context.user.id,
        CompetencyProgress.competency_id.in_(competency_ids or [UUID(int=0)]),
    )))
    evidence_rows = list(db.scalars(select(Evidence).where(Evidence.user_id == context.user.id)))

    lp_by_id = {item.lesson_id: item for item in lesson_progress}
    labs_by_module: dict[UUID, list[Lab]] = defaultdict(list)
    lab_map = {item.id: item for item in labs}
    for item in labs:
        labs_by_module[item.module_id].append(item)
    lab_attempts_by_id: dict[UUID, list[LabAttempt]] = defaultdict(list)
    for item in lab_attempts:
        lab_attempts_by_id[item.lab_id].append(item)
    assessments_by_module: dict[UUID, list[Assessment]] = defaultdict(list)
    for item in assessments:
        assessments_by_module[item.module_id].append(item)
    attempts_by_id: dict[UUID, list[AssessmentAttempt]] = defaultdict(list)
    for item in assessment_attempts:
        attempts_by_id[item.assessment_id].append(item)
    competencies_by_module: dict[UUID, list[Competency]] = defaultdict(list)
    for item in competencies:
        competencies_by_module[item.module_id].append(item)
    cp_by_id = {item.competency_id: item for item in competency_progress}

    lessons_by_module: dict[UUID, list[Lesson]] = defaultdict(list)
    for item in lessons:
        lessons_by_module[item.module_id].append(item)

    module_payload = []
    for module in modules:
        module_lessons = lessons_by_module[module.id]
        completed_lessons = sum(1 for item in module_lessons if lp_by_id.get(item.id) and lp_by_id[item.id].status == "completed")
        module_labs = labs_by_module[module.id]
        validated_labs = sum(1 for lab in module_labs if any(a.status == "validated" for a in lab_attempts_by_id[lab.id]))
        module_assessments = assessments_by_module[module.id]
        module_attempts = [a for assessment in module_assessments for a in attempts_by_id[assessment.id]]
        module_competencies = competencies_by_module[module.id]
        module_progress_rows = [cp_by_id[c.id] for c in module_competencies if c.id in cp_by_id]
        module_payload.append({
            "module_id": str(module.id), "module_code": module.code,
            "source_module_code": module.source_module_code, "title": module.title,
            "track_code": module.track.code if module.track else None,
            "estimated_hours": module.estimated_hours,
            "lessons_total": len(module_lessons), "lessons_completed": completed_lessons,
            "labs_total": len(module_labs), "labs_validated": validated_labs,
            "lab_attempts": sum(len(lab_attempts_by_id[item.id]) for item in module_labs),
            "assessments_total": len(module_assessments), "assessment_attempts": len(module_attempts),
            "assessment_reviews_pending": sum(1 for a in module_attempts if a.review_status in {"submitted", "in_review"}),
            "competencies_total": len(module_competencies),
            "competencies_mastered": sum(1 for p in module_progress_rows if p.status == "mastered"),
            "competencies_in_progress": sum(1 for p in module_progress_rows if p.status in {"in_progress", "self_assessed", "under_review"}),
        })

    summary = {
        "lessons_total": len(lessons),
        "lessons_completed": sum(1 for item in lesson_progress if item.status == "completed"),
        "labs_total": len(labs),
        "labs_validated": len({item.lab_id for item in lab_attempts if item.status == "validated"}),
        "lab_attempts": len(lab_attempts),
        "assessments_total": len(assessments),
        "assessment_attempts": len(assessment_attempts),
        "assessment_reviews_pending": sum(1 for item in assessment_attempts if item.review_status in {"submitted", "in_review"}),
        "assessments_passed": sum(1 for item in assessment_attempts if item.review_status == "reviewed" and item.passed),
        "competencies_total": len(competencies),
        "competencies_mastered": sum(1 for item in competency_progress if item.status == "mastered"),
        "competencies_in_progress": sum(1 for item in competency_progress if item.status in {"in_progress", "self_assessed", "under_review"}),
        "evidence_submitted": len(evidence_rows),
        "evidence_accepted": sum(1 for item in evidence_rows if item.review_status == "accepted"),
    }
    return {
        "user": {"id": str(context.user.id), "display_name": context.user.display_name, "email": context.user.email},
        "summary": summary,
        "modules": module_payload,
    }


@router.get("/modules/{module_code}/progress", dependencies=[Depends(require_permission("learning:read"))])
def get_module_progress(
    module_code: str,
    context: AuthContext = Depends(require_permission("learning:read")),
    db: Session = Depends(get_db),
) -> dict:
    module = _module_or_404(db, module_code)
    lessons = list(db.scalars(select(Lesson).where(Lesson.module_id == module.id).order_by(Lesson.sequence)))
    lesson_rows = list(db.scalars(select(LessonProgress).where(
        LessonProgress.user_id == context.user.id,
        LessonProgress.lesson_id.in_([item.id for item in lessons] or [UUID(int=0)]),
    )))
    lesson_map = {item.lesson_id: item for item in lesson_rows}

    labs = list(db.scalars(select(Lab).where(Lab.module_id == module.id)))
    lab_rows = list(db.scalars(select(LabAttempt).where(
        LabAttempt.user_id == context.user.id,
        LabAttempt.lab_id.in_([item.id for item in labs] or [UUID(int=0)]),
    ).order_by(LabAttempt.created_at.desc())))
    labs_map: dict[UUID, list[LabAttempt]] = defaultdict(list)
    for item in lab_rows:
        labs_map[item.lab_id].append(item)

    assessments = list(db.scalars(select(Assessment).where(Assessment.module_id == module.id)))
    assessment_rows = list(db.scalars(select(AssessmentAttempt).where(
        AssessmentAttempt.user_id == context.user.id,
        AssessmentAttempt.assessment_id.in_([item.id for item in assessments] or [UUID(int=0)]),
    ).order_by(AssessmentAttempt.submitted_at.desc())))
    assessment_map: dict[UUID, list[AssessmentAttempt]] = defaultdict(list)
    for item in assessment_rows:
        assessment_map[item.assessment_id].append(item)

    competencies = list(db.scalars(select(Competency).where(Competency.module_id == module.id).order_by(Competency.code)))
    cp_rows = list(db.scalars(select(CompetencyProgress).where(
        CompetencyProgress.user_id == context.user.id,
        CompetencyProgress.competency_id.in_([item.id for item in competencies] or [UUID(int=0)]),
    )))
    cp_map = {item.competency_id: item for item in cp_rows}
    evidence_rows = list(db.scalars(select(Evidence).where(
        Evidence.user_id == context.user.id,
        Evidence.competency_id.in_([item.id for item in competencies] or [UUID(int=0)]),
    ).order_by(Evidence.created_at.desc())))

    return {
        "module": {"code": module.code, "title": module.title, "estimated_hours": module.estimated_hours},
        "lessons": [_serialize_lesson_progress(item, lesson_map.get(item.id)) for item in lessons],
        "labs": [_serialize_lab(item, labs_map[item.id]) for item in labs],
        "assessments": [_serialize_assessment(item, assessment_map[item.id]) for item in assessments],
        "competencies": [_serialize_competency(item, cp_map.get(item.id)) for item in competencies],
        "evidence": [{
            "id": str(item.id), "competency_id": str(item.competency_id),
            "evidence_type": item.evidence_type, "title": item.title,
            "review_status": item.review_status, "summary": item.summary,
            "created_at": item.created_at.isoformat(),
        } for item in evidence_rows],
    }


@router.put("/lessons/{lesson_id}/progress")
def update_lesson_progress(
    lesson_id: UUID,
    payload: LessonProgressUpdate,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("learning:progress")),
    db: Session = Depends(get_db),
) -> dict:
    lesson = db.scalar(select(Lesson).where(Lesson.id == lesson_id))
    if lesson is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    now = datetime.now(timezone.utc)
    progress = db.scalar(select(LessonProgress).where(
        LessonProgress.user_id == context.user.id,
        LessonProgress.lesson_id == lesson_id,
    ).with_for_update())
    if progress is None:
        progress = LessonProgress(
            user_id=context.user.id, lesson_id=lesson_id,
            started_at=now, status="in_progress", completion_percent=0,
            time_spent_seconds=0, last_position={},
        )
        db.add(progress)
    if progress.status == "completed" and payload.status == "in_progress":
        raise HTTPException(status_code=409, detail="Uma aula concluída não pode ser reaberta por esta operação.")
    progress.status = payload.status
    progress.completion_percent = 100 if payload.status == "completed" else min(payload.completion_percent, 99.9)
    progress.time_spent_seconds = max(progress.time_spent_seconds, payload.time_spent_seconds)
    progress.last_position = payload.last_position
    if payload.status == "completed":
        progress.completed_at = progress.completed_at or now
    _audit(db, request, context.user.id, "learning.lesson.progress_updated", "lesson", str(lesson_id), {"status": progress.status})
    db.commit()
    return {"lesson_id": str(lesson_id), "status": progress.status, "completion_percent": progress.completion_percent}


@router.post("/labs/{lab_id}/attempts", status_code=status.HTTP_201_CREATED)
def start_lab_attempt(
    lab_id: UUID,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("labs:execute")),
    db: Session = Depends(get_db),
) -> dict:
    lab = db.scalar(select(Lab).where(Lab.id == lab_id))
    if lab is None:
        raise HTTPException(status_code=404, detail="Laboratório não encontrado.")
    now = datetime.now(timezone.utc)
    attempt = LabAttempt(user_id=context.user.id, lab_id=lab.id, status="started", started_at=now)
    db.add(attempt)
    db.flush()
    _audit(db, request, context.user.id, "learning.lab.started", "lab_attempt", str(attempt.id), {"lab_code": lab.code})
    db.commit()
    return {"id": str(attempt.id), "lab_id": str(lab.id), "status": attempt.status, "started_at": now.isoformat()}


@router.patch("/lab-attempts/{attempt_id}/submit")
def submit_lab_attempt(
    attempt_id: UUID,
    payload: LabAttemptSubmit,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("learning:progress")),
    db: Session = Depends(get_db),
) -> dict:
    attempt = db.scalar(select(LabAttempt).where(
        LabAttempt.id == attempt_id, LabAttempt.user_id == context.user.id
    ).with_for_update())
    if attempt is None:
        raise HTTPException(status_code=404, detail="Tentativa de laboratório não encontrada.")
    if attempt.status not in {"started", "returned"}:
        raise HTTPException(status_code=409, detail="A tentativa não está num estado que permita submissão.")
    attempt.status = "submitted"
    attempt.learner_notes = payload.learner_notes.strip()
    attempt.submission = payload.submission
    attempt.submitted_at = datetime.now(timezone.utc)
    _audit(db, request, context.user.id, "learning.lab.submitted", "lab_attempt", str(attempt.id))
    db.commit()
    return {"id": str(attempt.id), "status": attempt.status, "submitted_at": attempt.submitted_at.isoformat()}


@router.post("/lab-attempts/{attempt_id}/review")
def review_lab_attempt(
    attempt_id: UUID,
    payload: LabAttemptReview,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("labs:review")),
    db: Session = Depends(get_db),
) -> dict:
    attempt = db.scalar(select(LabAttempt).where(LabAttempt.id == attempt_id).with_for_update())
    if attempt is None:
        raise HTTPException(status_code=404, detail="Tentativa de laboratório não encontrada.")
    if attempt.user_id == context.user.id:
        raise HTTPException(status_code=403, detail="Separação de funções: não podes rever a tua própria submissão.")
    if attempt.status not in {"submitted", "in_review"}:
        raise HTTPException(status_code=409, detail="Só é possível rever uma tentativa submetida.")
    attempt.status = payload.outcome
    attempt.validation_report = payload.validation_report
    attempt.reviewed_by_user_id = context.user.id
    attempt.reviewed_at = datetime.now(timezone.utc)
    _audit(db, request, context.user.id, "learning.lab.reviewed", "lab_attempt", str(attempt.id), {"outcome": payload.outcome})
    db.commit()
    return {"id": str(attempt.id), "status": attempt.status, "reviewed_at": attempt.reviewed_at.isoformat()}


@router.post("/assessments/{assessment_id}/attempts", status_code=status.HTTP_201_CREATED)
def submit_assessment_attempt(
    assessment_id: UUID,
    payload: AssessmentAttemptCreate,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("assessments:attempt")),
    db: Session = Depends(get_db),
) -> dict:
    assessment = db.scalar(select(Assessment).where(Assessment.id == assessment_id))
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        learner_key=str(context.user.id),
        user_id=context.user.id,
        score=0,
        passed=False,
        review_status="submitted",
        answers=payload.answers,
        feedback={},
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()
    _audit(db, request, context.user.id, "learning.assessment.submitted", "assessment_attempt", str(attempt.id), {"assessment_code": assessment.code})
    db.commit()
    return {"id": str(attempt.id), "assessment_id": str(assessment.id), "review_status": attempt.review_status, "submitted_at": attempt.submitted_at.isoformat()}


@router.post("/assessment-attempts/{attempt_id}/review")
def review_assessment_attempt(
    attempt_id: UUID,
    payload: AssessmentAttemptReview,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("assessments:review")),
    db: Session = Depends(get_db),
) -> dict:
    attempt = db.scalar(select(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id).with_for_update())
    if attempt is None:
        raise HTTPException(status_code=404, detail="Tentativa de avaliação não encontrada.")
    if attempt.user_id == context.user.id:
        raise HTTPException(status_code=403, detail="Separação de funções: não podes corrigir a tua própria avaliação.")
    if attempt.review_status not in {"submitted", "in_review", "returned"}:
        raise HTTPException(status_code=409, detail="Esta tentativa já foi revista.")
    assessment = db.scalar(select(Assessment).where(Assessment.id == attempt.assessment_id))
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação associada não encontrada.")
    if payload.score > assessment.total_points:
        raise HTTPException(status_code=422, detail=f"A nota não pode exceder {assessment.total_points} pontos.")
    attempt.score = payload.score
    attempt.passed = payload.score >= assessment.mastery_threshold
    attempt.review_status = "reviewed"
    attempt.feedback = payload.feedback
    attempt.reviewed_by_user_id = context.user.id
    attempt.reviewed_at = datetime.now(timezone.utc)
    _audit(db, request, context.user.id, "learning.assessment.reviewed", "assessment_attempt", str(attempt.id), {"score": payload.score, "passed": attempt.passed})
    db.commit()
    return {"id": str(attempt.id), "review_status": attempt.review_status, "score": attempt.score, "passed": attempt.passed}


@router.put("/competencies/{competency_id}/self-assessment")
def update_competency_self_assessment(
    competency_id: UUID,
    payload: CompetencySelfAssessment,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("learning:progress")),
    db: Session = Depends(get_db),
) -> dict:
    competency = db.scalar(select(Competency).where(Competency.id == competency_id))
    if competency is None:
        raise HTTPException(status_code=404, detail="Competência não encontrada.")
    progress = db.scalar(select(CompetencyProgress).where(
        CompetencyProgress.user_id == context.user.id,
        CompetencyProgress.competency_id == competency_id,
    ).with_for_update())
    if progress is None:
        progress = CompetencyProgress(
            competency_id=competency_id,
            learner_key=str(context.user.id),
            user_id=context.user.id,
            status=payload.status,
            self_assessment_notes=payload.notes.strip(),
        )
        db.add(progress)
    else:
        if progress.status in {"mastered", "demonstrated"}:
            raise HTTPException(status_code=409, detail="Uma competência validada só pode ser alterada por revisão técnica.")
        progress.status = payload.status
        progress.self_assessment_notes = payload.notes.strip()
    _audit(db, request, context.user.id, "learning.competency.self_assessed", "competency", str(competency_id), {"status": payload.status})
    db.commit()
    return {"competency_id": str(competency_id), "status": progress.status}


@router.post("/competencies/{competency_id}/review")
def review_competency(
    competency_id: UUID,
    payload: CompetencyReview,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("assessments:review")),
    db: Session = Depends(get_db),
) -> dict:
    if payload.learner_user_id == context.user.id:
        raise HTTPException(status_code=403, detail="Separação de funções: não podes validar a tua própria competência.")
    learner = db.scalar(select(User).where(User.id == payload.learner_user_id, User.status == "active"))
    if learner is None:
        raise HTTPException(status_code=404, detail="Estudante ativo não encontrado.")
    competency = db.scalar(select(Competency).where(Competency.id == competency_id))
    if competency is None:
        raise HTTPException(status_code=404, detail="Competência não encontrada.")
    progress = db.scalar(select(CompetencyProgress).where(
        CompetencyProgress.user_id == learner.id,
        CompetencyProgress.competency_id == competency_id,
    ).with_for_update())
    if progress is None or progress.status != "self_assessed":
        raise HTTPException(status_code=409, detail="Só é possível rever uma competência que o estudante tenha submetido para revisão.")

    passed_attempt = db.scalar(
        select(AssessmentAttempt.id)
        .join(assessment_competencies, assessment_competencies.c.assessment_id == AssessmentAttempt.assessment_id)
        .where(
            assessment_competencies.c.competency_id == competency_id,
            AssessmentAttempt.user_id == learner.id,
            AssessmentAttempt.review_status == "reviewed",
            AssessmentAttempt.passed.is_(True),
        ).limit(1)
    )
    accepted_evidence = db.scalar(select(Evidence.id).where(
        Evidence.user_id == learner.id,
        Evidence.competency_id == competency_id,
        Evidence.review_status == "accepted",
    ).limit(1))
    validated_lab = db.scalar(
        select(LabAttempt.id)
        .join(Lab, Lab.id == LabAttempt.lab_id)
        .join(lab_competencies, lab_competencies.c.lab_id == Lab.id)
        .where(
            lab_competencies.c.competency_id == competency_id,
            LabAttempt.user_id == learner.id,
            LabAttempt.status == "validated",
        ).limit(1)
    )
    has_reviewed_proof = bool(passed_attempt or accepted_evidence or validated_lab)

    if payload.status in {"demonstrated", "mastered"} and not has_reviewed_proof:
        raise HTTPException(status_code=409, detail="A validação exige avaliação aprovada, evidência aceite ou laboratório validado por um Reviewer.")

    if payload.status == "mastered":
        if payload.mastery_score is None:
            raise HTTPException(status_code=422, detail="Para marcar domínio, é obrigatória uma nota de domínio.")
        linked_threshold = db.scalar(
            select(func.max(Assessment.mastery_threshold))
            .join(assessment_competencies, assessment_competencies.c.assessment_id == Assessment.id)
            .where(assessment_competencies.c.competency_id == competency_id)
        )
        required_threshold = float(linked_threshold if linked_threshold is not None else 80.0)
        if payload.mastery_score < required_threshold:
            raise HTTPException(status_code=422, detail=f"A nota de domínio deve ser pelo menos {required_threshold:g}/100, conforme a avaliação associada.")
        if not passed_attempt and not accepted_evidence:
            raise HTTPException(status_code=409, detail="O domínio exige avaliação aprovada ou evidência aceite; um laboratório validado isoladamente não basta.")

    progress.status = payload.status
    progress.mastery_score = payload.mastery_score if payload.status == "mastered" else None
    progress.notes = payload.notes.strip()
    progress.last_assessed_at = datetime.now(timezone.utc)
    _audit(db, request, context.user.id, "learning.competency.reviewed", "competency_progress", str(progress.id), {
        "learner_user_id": str(learner.id), "competency_id": str(competency_id),
        "status": payload.status, "mastery_score": progress.mastery_score,
    })
    db.commit()
    return {"competency_id": str(competency_id), "learner_user_id": str(learner.id), "status": progress.status, "mastery_score": progress.mastery_score}


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
def submit_evidence(
    payload: EvidenceCreate,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("portfolio:manage")),
    db: Session = Depends(get_db),
) -> dict:
    sources = [payload.lesson_id, payload.lab_id, payload.assessment_attempt_id]
    if sum(item is not None for item in sources) != 1:
        raise HTTPException(status_code=422, detail="Indica exatamente uma origem: aula, laboratório ou tentativa de avaliação.")
    competency = db.scalar(select(Competency).where(Competency.id == payload.competency_id))
    if competency is None:
        raise HTTPException(status_code=404, detail="Competência não encontrada.")
    lesson_id = payload.lesson_id
    lab_id = payload.lab_id
    assessment_attempt_id = payload.assessment_attempt_id
    if lesson_id:
        lesson = db.scalar(select(Lesson).where(Lesson.id == lesson_id, Lesson.module_id == competency.module_id))
        linked = db.scalar(select(lesson_competencies.c.lesson_id).where(
            lesson_competencies.c.lesson_id == lesson_id,
            lesson_competencies.c.competency_id == competency.id,
        ))
        completed = db.scalar(select(LessonProgress.id).where(
            LessonProgress.user_id == context.user.id, LessonProgress.lesson_id == lesson_id,
            LessonProgress.status == "completed",
        ))
        if lesson is None or completed is None or linked is None:
            raise HTTPException(status_code=409, detail="A evidência de aula exige uma aula concluída e explicitamente ligada à competência.")
    if lab_id:
        lab = db.scalar(select(Lab).where(Lab.id == lab_id, Lab.module_id == competency.module_id))
        linked = db.scalar(select(lab_competencies.c.lab_id).where(
            lab_competencies.c.lab_id == lab_id,
            lab_competencies.c.competency_id == competency.id,
        ))
        submitted = db.scalar(select(LabAttempt.id).where(
            LabAttempt.user_id == context.user.id, LabAttempt.lab_id == lab_id,
            LabAttempt.status.in_(["submitted", "validated"]),
        ).limit(1))
        if lab is None or submitted is None or linked is None:
            raise HTTPException(status_code=409, detail="A evidência de laboratório exige uma tentativa submetida e um vínculo explícito com a competência.")
    if assessment_attempt_id:
        attempt = db.scalar(select(AssessmentAttempt).where(
            AssessmentAttempt.id == assessment_attempt_id, AssessmentAttempt.user_id == context.user.id,
        ))
        if attempt is None:
            raise HTTPException(status_code=404, detail="Tentativa de avaliação não encontrada para este utilizador.")
        linked = db.scalar(select(assessment_competencies.c.competency_id).where(
            assessment_competencies.c.assessment_id == attempt.assessment_id,
            assessment_competencies.c.competency_id == competency.id,
        ))
        assessment = db.scalar(select(Assessment).where(Assessment.id == attempt.assessment_id, Assessment.module_id == competency.module_id))
        if linked is None or assessment is None:
            raise HTTPException(status_code=409, detail="A avaliação não está ligada à competência indicada.")
    evidence = Evidence(
        competency_id=competency.id,
        user_id=context.user.id,
        lesson_id=lesson_id,
        lab_id=lab_id,
        assessment_attempt_id=assessment_attempt_id,
        evidence_type=payload.evidence_type,
        title=payload.title.strip(),
        artifact_uri=payload.artifact_uri,
        summary=payload.summary.strip(),
        sanitized=False,
        review_status="pending",
        metadata_json={},
    )
    db.add(evidence)
    db.flush()
    _audit(db, request, context.user.id, "learning.evidence.submitted", "evidence", str(evidence.id), {"competency_id": str(competency.id)})
    db.commit()
    return {"id": str(evidence.id), "competency_id": str(competency.id), "review_status": evidence.review_status}


@router.post("/evidence/{evidence_id}/review")
def review_evidence(
    evidence_id: UUID,
    payload: EvidenceReview,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("portfolio:review")),
    db: Session = Depends(get_db),
) -> dict:
    evidence = db.scalar(select(Evidence).where(Evidence.id == evidence_id).with_for_update())
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidência não encontrada.")
    if evidence.user_id == context.user.id:
        raise HTTPException(status_code=403, detail="Separação de funções: não podes rever a tua própria evidência.")
    if evidence.review_status != "pending":
        raise HTTPException(status_code=409, detail="Esta evidência já foi revista ou deixou o estado pendente.")
    evidence.review_status = payload.review_status
    evidence.reviewed_by_user_id = context.user.id
    evidence.reviewed_at = datetime.now(timezone.utc)
    metadata = dict(evidence.metadata_json or {})
    metadata["review_note"] = payload.review_note.strip()
    evidence.metadata_json = metadata
    _audit(db, request, context.user.id, "learning.evidence.reviewed", "evidence", str(evidence.id), {"review_status": payload.review_status})
    db.commit()
    return {"id": str(evidence.id), "review_status": evidence.review_status}


@router.get("/review-queue", dependencies=[Depends(require_permission("assessments:review"))])
def get_review_queue(
    context: AuthContext = Depends(require_permission("assessments:review")),
    db: Session = Depends(get_db),
) -> dict:
    pending_labs = db.execute(
        select(LabAttempt, Lab, User)
        .join(Lab, Lab.id == LabAttempt.lab_id)
        .join(User, User.id == LabAttempt.user_id)
        .where(
            LabAttempt.status.in_(["submitted", "in_review"]),
            LabAttempt.user_id != context.user.id,
        )
        .order_by(LabAttempt.submitted_at.asc())
    ).all()
    pending_assessments = db.execute(
        select(AssessmentAttempt, Assessment, User)
        .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
        .join(User, User.id == AssessmentAttempt.user_id)
        .where(
            AssessmentAttempt.review_status.in_(["submitted", "in_review", "returned"]),
            AssessmentAttempt.user_id != context.user.id,
        )
        .order_by(AssessmentAttempt.submitted_at.asc())
    ).all()
    pending_evidence = db.execute(
        select(Evidence, Competency, User)
        .join(Competency, Competency.id == Evidence.competency_id)
        .join(User, User.id == Evidence.user_id)
        .where(Evidence.review_status == "pending", Evidence.user_id != context.user.id)
        .order_by(Evidence.created_at.asc())
    ).all()
    pending_competencies = db.execute(
        select(CompetencyProgress, Competency, User)
        .join(Competency, Competency.id == CompetencyProgress.competency_id)
        .join(User, User.id == CompetencyProgress.user_id)
        .where(CompetencyProgress.status == "self_assessed", CompetencyProgress.user_id != context.user.id)
        .order_by(CompetencyProgress.updated_at.asc())
    ).all()
    return {
        "lab_attempts": [{
            "id": str(attempt.id), "status": attempt.status, "lab_code": lab.code,
            "lab_title": lab.title, "learner_name": learner.display_name,
            "learner_email": learner.email, "learner_notes": attempt.learner_notes,
            "submission": attempt.submission, "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        } for attempt, lab, learner in pending_labs],
        "assessment_attempts": [{
            "id": str(attempt.id), "status": attempt.review_status,
            "assessment_code": assessment.code, "assessment_title": assessment.title,
            "total_points": assessment.total_points, "mastery_threshold": assessment.mastery_threshold,
            "questions": assessment.rubric.get("questions", []),
            "learner_name": learner.display_name, "learner_email": learner.email,
            "answers": attempt.answers, "submitted_at": attempt.submitted_at.isoformat(),
        } for attempt, assessment, learner in pending_assessments],
        "evidence": [{
            "id": str(item.id), "title": item.title, "evidence_type": item.evidence_type,
            "summary": item.summary, "artifact_uri": item.artifact_uri,
            "competency_code": competency.code, "competency_title": competency.title,
            "learner_name": learner.display_name, "learner_email": learner.email,
            "created_at": item.created_at.isoformat(),
        } for item, competency, learner in pending_evidence],
        "competency_reviews": [{
            "competency_id": str(competency.id), "competency_code": competency.code,
            "competency_title": competency.title, "learner_user_id": str(learner.id),
            "learner_name": learner.display_name, "learner_email": learner.email,
            "self_assessment_notes": progress.self_assessment_notes,
            "updated_at": progress.updated_at.isoformat(),
        } for progress, competency, learner in pending_competencies],
    }

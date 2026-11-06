from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.auth_dependencies import AuthContext, get_current_auth_context, require_csrf, require_permission
from app.models import (
    Assessment, Competency, CoverageRequirement, CurriculumBlock,
    CurriculumModule, CurriculumTopic, CurriculumTrack, CurriculumVersion, Evidence, Lab,
    Lesson, InternshipTicket, CompetencyProgress, LearningResource,
)
from app.models.curriculum import (
    assessment_competencies, competency_prerequisites, lab_competencies,
    lesson_competencies, ticket_competencies,
)

router = APIRouter(dependencies=[Depends(get_current_auth_context)])

LEARNING_REQUIREMENTS = [
    ("definition", "Definição, finalidade e contexto"),
    ("prerequisites", "Pré-requisitos e dependências"),
    ("terminology", "Terminologia técnica explicada"),
    ("internal_behaviour", "Funcionamento interno e mecanismos"),
    ("standards_protocols", "Normas, padrões e protocolos relevantes"),
    ("official_documentation", "Documentação oficial e versão"),
    ("practical_examples", "Exemplos práticos"),
    ("guided_lab", "Laboratório guiado"),
    ("independent_exercise", "Exercício individual"),
    ("troubleshooting", "Cenário de troubleshooting"),
    ("security_context", "Relevância de segurança e controlos aplicáveis"),
    ("theory_assessment", "Avaliação teórica"),
    ("practical_assessment", "Avaliação prática"),
    ("evidence", "Evidência verificável de competência"),
]

INTERNSHIP_REQUIREMENTS = [
    ("company_context", "Contexto da empresa e do serviço"),
    ("responsible_role", "Função e responsabilidade profissional"),
    ("affected_assets", "Ativos e sistemas afetados"),
    ("ticket_request", "Ticket, pedido, incidente ou mudança"),
    ("initial_state", "Estado inicial reproduzível"),
    ("investigation", "Investigação e recolha de evidências"),
    ("execution", "Procedimento de execução ou correção"),
    ("validation", "Validação técnica"),
    ("acceptance_criteria", "Critérios de aceitação mensuráveis"),
    ("technical_review", "Revisão técnica"),
    ("documentation", "Documentação profissional"),
    ("evidence", "Evidência associada à competência"),
]


class TopicCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=3, max_length=220)
    position: int = Field(ge=1)
    description: str | None = None


class ResourceCreate(BaseModel):
    competency_id: UUID | None = None
    resource_type: str = Field(pattern="^(official_documentation|standard|reference|book|video|article)$")
    title: str = Field(min_length=3, max_length=240)
    url: str = Field(min_length=8, max_length=1000)
    publisher: str | None = None
    product_version: str | None = None


class CoverageStatusUpdate(BaseModel):
    status: str = Field(pattern="^(missing|draft|ready)$")
    reviewer_note: str | None = None


class CompetencyCreate(BaseModel):
    code: str = Field(min_length=3, max_length=100)
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    topic_id: UUID | None = None
    prerequisite_ids: list[UUID] = Field(default_factory=list)
    is_security_relevant: bool = False


class LessonCreate(BaseModel):
    code: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=3, max_length=240)
    sequence: int = Field(ge=1)
    summary: str | None = None
    content_markdown: str | None = None
    status: str = Field(default="draft", pattern="^(draft|in_review|ready)$")
    competency_ids: list[UUID] = Field(default_factory=list)


class LabCreate(BaseModel):
    code: str = Field(min_length=3, max_length=100)
    title: str = Field(min_length=3, max_length=240)
    description: str | None = None
    environment: str = "WSL2 Ubuntu 24.04"
    safety_profile: str = "local-safe"
    estimated_minutes: int | None = Field(default=None, ge=1)
    manifest: dict = Field(default_factory=dict)
    competency_ids: list[UUID] = Field(default_factory=list)


class TicketCreate(BaseModel):
    ticket_key: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=240)
    department: str = Field(min_length=2, max_length=100)
    priority: str = "normal"
    description: str = Field(min_length=10)
    business_impact: str | None = None
    asset_context: str | None = None
    assigned_role: str | None = None
    initial_state: str | None = None
    investigation_steps: list[str] = Field(default_factory=list)
    execution_steps: list[str] = Field(default_factory=list)
    validation_steps: list[str] = Field(default_factory=list)
    safety_scope: str | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    competency_ids: list[UUID] = Field(default_factory=list)


class AssessmentCreate(BaseModel):
    code: str = Field(min_length=3, max_length=100)
    title: str = Field(min_length=3, max_length=240)
    assessment_type: str = Field(pattern="^(theory|practical|oral|mixed|final)$")
    total_points: int = Field(default=100, ge=1)
    mastery_threshold: float = Field(default=80.0, ge=0, le=100)
    rubric: dict = Field(default_factory=dict)
    competency_ids: list[UUID] = Field(default_factory=list)


def _ensure_competencies_belong_to_module(db: Session, module_id: UUID, ids: list[UUID]) -> list[Competency]:
    if not ids:
        return []
    unique_ids = list(dict.fromkeys(ids))
    rows = list(db.scalars(select(Competency).where(
        Competency.id.in_(unique_ids), Competency.module_id == module_id
    )))
    if len(rows) != len(unique_ids):
        raise HTTPException(status_code=422, detail="Uma ou mais competências não pertencem a este módulo.")
    return rows


def _module_or_404(db: Session, module_code: str) -> CurriculumModule:
    module = db.scalar(select(CurriculumModule).where(CurriculumModule.code == module_code))
    if module is None:
        raise HTTPException(status_code=404, detail="Módulo curricular não encontrado.")
    return module


def _mark_module_as_draft(module: CurriculumModule) -> None:
    if module.content_status == "not_authored":
        module.content_status = "draft"


@router.get("/catalog", dependencies=[Depends(require_permission("learning:read"))])
def get_catalog(db: Session = Depends(get_db)) -> dict:
    tracks = list(db.scalars(select(CurriculumTrack).where(CurriculumTrack.is_active.is_(True)).order_by(CurriculumTrack.position)))
    version = db.scalar(select(CurriculumVersion).where(CurriculumVersion.status == "active").order_by(CurriculumVersion.created_at.desc()))
    catalog_tracks = []
    totals = {"tracks": len(tracks), "blocks": 0, "modules": 0, "estimated_module_hours": 0, "competencies": 0, "lessons": 0, "labs": 0, "tickets": 0, "assessments": 0, "resources": 0}

    for track in tracks:
        blocks = list(db.scalars(select(CurriculumBlock).where(CurriculumBlock.track_id == track.id).order_by(CurriculumBlock.position)))
        modules = list(db.scalars(select(CurriculumModule).where(CurriculumModule.track_id == track.id).order_by(CurriculumModule.position)))
        blocks_payload = []
        for block in blocks:
            block_modules = [m for m in modules if m.block_id == block.id]
            blocks_payload.append({
                "id": str(block.id), "code": block.code, "title": block.title,
                "position": block.position,
                "modules": [{
                    "id": str(m.id), "code": m.code, "source_module_code": m.source_module_code,
                    "title": m.title, "position": m.position, "estimated_hours": m.estimated_hours,
                    "content_status": m.content_status, "source_verified": m.source_verified,
                    "competency_count": db.query(Competency).filter(Competency.module_id == m.id).count(),
                    "lesson_count": db.query(Lesson).filter(Lesson.module_id == m.id).count(),
                    "lab_count": db.query(Lab).filter(Lab.module_id == m.id).count(),
                    "ticket_count": db.query(InternshipTicket).filter(InternshipTicket.module_id == m.id).count(),
                    "assessment_count": db.query(Assessment).filter(Assessment.module_id == m.id).count(),
                } for m in block_modules],
            })
        track_modules = [m for m in modules]
        totals["blocks"] += len(blocks)
        totals["modules"] += len(modules)
        totals["estimated_module_hours"] += sum(m.estimated_hours or 0 for m in modules)
        for key, model in [("competencies", Competency), ("lessons", Lesson), ("labs", Lab), ("tickets", InternshipTicket), ("assessments", Assessment), ("resources", LearningResource)]:
            if track_modules:
                totals[key] += db.query(model).filter(model.module_id.in_([m.id for m in track_modules])).count()
        environment_labs = list(db.scalars(select(Lab).where(Lab.track_id == track.id, Lab.module_id.is_(None))))
        catalog_tracks.append({
            "id": str(track.id), "code": track.code, "title": track.title,
            "description": track.description, "position": track.position,
            "blocks": blocks_payload,
            "environment_labs": [{
                "id": str(lab.id), "code": lab.code, "title": lab.title,
                "estimated_minutes": lab.estimated_minutes, "status": lab.status,
            } for lab in environment_labs],
        })
        totals["labs"] += len(environment_labs)

    return {
        "version": {
            "code": version.code, "title": version.title,
            "source_filename": version.source_filename, "status": version.status,
        } if version else None,
        "summary": totals,
        "tracks": catalog_tracks,
        "integrity": {
            "canonical_order_preserved": True,
            "has_any_authored_lessons": totals["lessons"] > 0,
            "note": "Estrutura do mapa importada. As aulas, competências, laboratórios de módulo, tickets e avaliações só serão contabilizados quando forem efetivamente criados e associados.",
        },
    }


@router.get("/modules/{module_code}", dependencies=[Depends(require_permission("learning:read"))])
def get_module_detail(module_code: str, db: Session = Depends(get_db)) -> dict:
    module = _module_or_404(db, module_code)
    block = db.get(CurriculumBlock, module.block_id) if module.block_id else None
    competencies = list(db.scalars(select(Competency).where(Competency.module_id == module.id).order_by(Competency.code)))
    lessons = list(db.scalars(select(Lesson).where(Lesson.module_id == module.id).order_by(Lesson.sequence)))
    labs = list(db.scalars(select(Lab).where(Lab.module_id == module.id).order_by(Lab.code)))
    assessments = list(db.scalars(select(Assessment).where(Assessment.module_id == module.id).order_by(Assessment.code)))
    tickets = list(db.scalars(select(InternshipTicket).where(InternshipTicket.module_id == module.id).order_by(InternshipTicket.ticket_key)))
    return {
        "id": str(module.id), "code": module.code, "source_module_code": module.source_module_code,
        "title": module.title, "position": module.position, "estimated_hours": module.estimated_hours,
        "content_status": module.content_status, "block": block.code if block else None,
        "competencies": [{"id": str(c.id), "code": c.code, "title": c.title, "description": c.description, "is_security_relevant": c.is_security_relevant} for c in competencies],
        "lessons": [{
            "id": str(x.id), "code": x.code, "title": x.title, "sequence": x.sequence,
            "summary": x.summary, "content_markdown": x.content_markdown, "status": x.status,
        } for x in lessons],
        "labs": [{
            "id": str(x.id), "code": x.code, "title": x.title, "description": x.description,
            "status": x.status, "safety_profile": x.safety_profile,
            "environment": x.environment, "estimated_minutes": x.estimated_minutes,
            "manifest": x.manifest,
        } for x in labs],
        "tickets": [{
            "id": str(x.id), "ticket_key": x.ticket_key, "title": x.title,
            "department": x.department, "priority": x.priority, "status": x.status,
            "description": x.description, "business_impact": x.business_impact,
            "asset_context": x.asset_context, "assigned_role": x.assigned_role,
            "initial_state": x.initial_state, "investigation_steps": x.investigation_steps,
            "execution_steps": x.execution_steps, "validation_steps": x.validation_steps,
            "safety_scope": x.safety_scope, "acceptance_criteria": x.acceptance_criteria,
        } for x in tickets],
        "assessments": [{
            "id": str(x.id), "code": x.code, "title": x.title,
            "assessment_type": x.assessment_type, "status": x.status,
            "total_points": x.total_points, "mastery_threshold": x.mastery_threshold,
            "rubric": x.rubric,
        } for x in assessments],
        "topics": [{"id": str(x.id), "code": x.code, "title": x.title, "position": x.position, "description": x.description} for x in db.scalars(select(CurriculumTopic).where(CurriculumTopic.module_id == module.id).order_by(CurriculumTopic.position))],
        "resources": [{"id": str(x.id), "title": x.title, "resource_type": x.resource_type, "url": x.url, "publisher": x.publisher, "product_version": x.product_version} for x in db.scalars(select(LearningResource).where(LearningResource.module_id == module.id).order_by(LearningResource.title))],
    }


@router.get("/tickets", dependencies=[Depends(require_permission("tickets:read"))])
def list_internship_tickets(db: Session = Depends(get_db)) -> dict:
    rows = list(db.scalars(select(InternshipTicket).order_by(InternshipTicket.created_at.desc())))
    payload = []
    for ticket in rows:
        module = db.get(CurriculumModule, ticket.module_id) if ticket.module_id else None
        payload.append({
            "id": str(ticket.id),
            "ticket_key": ticket.ticket_key,
            "title": ticket.title,
            "department": ticket.department,
            "priority": ticket.priority,
            "status": ticket.status,
            "description": ticket.description,
            "business_impact": ticket.business_impact,
            "asset_context": ticket.asset_context,
            "assigned_role": ticket.assigned_role,
            "initial_state": ticket.initial_state,
            "investigation_steps": ticket.investigation_steps,
            "execution_steps": ticket.execution_steps,
            "validation_steps": ticket.validation_steps,
            "safety_scope": ticket.safety_scope,
            "acceptance_criteria": ticket.acceptance_criteria,
            "module_code": module.code if module else None,
            "module_title": module.title if module else None,
        })
    return {"count": len(payload), "tickets": payload}


@router.get("/coverage/summary", dependencies=[Depends(require_permission("learning:read"))])
def get_coverage_summary(db: Session = Depends(get_db)) -> dict:
    competencies = db.query(Competency).count()
    learning_rows = db.query(CoverageRequirement).filter(CoverageRequirement.center == "learning")
    internship_rows = db.query(CoverageRequirement).filter(CoverageRequirement.center == "internship")
    return {
        "competencies": competencies,
        "learning": {
            "requirements": learning_rows.count(),
            "verified": learning_rows.filter(CoverageRequirement.status == "verified").count(),
            "missing": learning_rows.filter(CoverageRequirement.status == "missing").count(),
        },
        "internship": {
            "requirements": internship_rows.count(),
            "verified": internship_rows.filter(CoverageRequirement.status == "verified").count(),
            "missing": internship_rows.filter(CoverageRequirement.status == "missing").count(),
        },
        "policy": "Nenhuma competência pode ser marcada como dominada apenas por visualização ou quiz; exige explicação, aplicação independente, troubleshooting e evidência revista.",
    }


@router.get("/competencies/{competency_code}/traceability", dependencies=[Depends(require_permission("learning:read"))])
def get_competency_traceability(
    competency_code: str,
    context: AuthContext = Depends(get_current_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    competency = db.scalar(select(Competency).where(Competency.code == competency_code))
    if competency is None:
        raise HTTPException(status_code=404, detail="Competência não encontrada.")
    lesson_rows = db.execute(select(Lesson).join(lesson_competencies).where(lesson_competencies.c.competency_id == competency.id)).scalars().all()
    lab_rows = db.execute(select(Lab).join(lab_competencies).where(lab_competencies.c.competency_id == competency.id)).scalars().all()
    ticket_rows = db.execute(select(InternshipTicket).join(ticket_competencies).where(ticket_competencies.c.competency_id == competency.id)).scalars().all()
    assessment_rows = db.execute(select(Assessment).join(assessment_competencies).where(assessment_competencies.c.competency_id == competency.id)).scalars().all()
    coverage_rows = list(db.scalars(select(CoverageRequirement).where(CoverageRequirement.competency_id == competency.id)))
    evidence_rows = list(db.scalars(select(Evidence).where(
        Evidence.competency_id == competency.id,
        Evidence.user_id == context.user.id,
    )))
    progress = db.scalar(select(CompetencyProgress).where(
        CompetencyProgress.competency_id == competency.id,
        CompetencyProgress.user_id == context.user.id,
    ))
    resource_rows = list(db.scalars(select(LearningResource).where(LearningResource.competency_id == competency.id)))
    return {
        "competency": {"id": str(competency.id), "code": competency.code, "title": competency.title, "description": competency.description},
        "prerequisites": [
            {"id": str(item.id), "code": item.code, "title": item.title}
            for item in db.scalars(select(Competency).join(competency_prerequisites, Competency.id == competency_prerequisites.c.prerequisite_id).where(competency_prerequisites.c.competency_id == competency.id))
        ],
        "learning": {"lessons": [{"id": str(x.id), "code": x.code, "title": x.title} for x in lesson_rows], "labs": [{"id": str(x.id), "code": x.code, "title": x.title} for x in lab_rows], "assessments": [{"id": str(x.id), "code": x.code, "title": x.title} for x in assessment_rows], "resources": [{"id": str(x.id), "title": x.title, "url": x.url, "resource_type": x.resource_type} for x in resource_rows]},
        "internship": {"tickets": [{"id": str(x.id), "ticket_key": x.ticket_key, "title": x.title, "status": x.status} for x in ticket_rows]},
        "coverage": [{"center": x.center, "requirement_code": x.requirement_code, "title": x.title, "required": x.is_required, "status": x.status} for x in coverage_rows],
        "evidence": [{"id": str(x.id), "title": x.title, "evidence_type": x.evidence_type, "review_status": x.review_status, "sanitized": x.sanitized} for x in evidence_rows],
        "progress": {"status": progress.status, "mastery_score": progress.mastery_score} if progress else {"status": "not_started", "mastery_score": None},
    }


@router.post("/modules/{module_code}/topics", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf), Depends(require_permission("platform:admin"))])
def create_topic(module_code: str, payload: TopicCreate, db: Session = Depends(get_db)) -> dict:
    module = _module_or_404(db, module_code)
    if db.scalar(select(CurriculumTopic).where(CurriculumTopic.module_id == module.id, CurriculumTopic.code == payload.code)):
        raise HTTPException(status_code=409, detail="Já existe um tópico com esse código neste módulo.")
    topic = CurriculumTopic(module_id=module.id, code=payload.code, title=payload.title, position=payload.position, description=payload.description)
    db.add(topic)
    _mark_module_as_draft(module)
    db.commit()
    return {"id": str(topic.id), "code": topic.code, "title": topic.title}


@router.post("/modules/{module_code}/resources", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf), Depends(require_permission("platform:admin"))])
def create_learning_resource(module_code: str, payload: ResourceCreate, db: Session = Depends(get_db)) -> dict:
    module = _module_or_404(db, module_code)
    if payload.competency_id:
        competency = db.get(Competency, payload.competency_id)
        if competency is None or competency.module_id != module.id:
            raise HTTPException(status_code=422, detail="A competência indicada não pertence ao módulo.")
    if not payload.url.startswith(("https://", "http://")):
        raise HTTPException(status_code=422, detail="A referência deve usar um URL HTTP ou HTTPS explícito.")
    resource = LearningResource(
        module_id=module.id, competency_id=payload.competency_id,
        resource_type=payload.resource_type, title=payload.title, url=payload.url,
        publisher=payload.publisher, product_version=payload.product_version,
    )
    db.add(resource)
    _mark_module_as_draft(module)
    db.commit()
    return {"id": str(resource.id), "title": resource.title, "resource_type": resource.resource_type}


@router.patch("/coverage/{coverage_id}", dependencies=[Depends(require_csrf), Depends(require_permission("platform:admin"))])
def update_coverage_status(coverage_id: UUID, payload: CoverageStatusUpdate, db: Session = Depends(get_db)) -> dict:
    coverage = db.get(CoverageRequirement, coverage_id)
    if coverage is None:
        raise HTTPException(status_code=404, detail="Requisito de cobertura não encontrado.")
    # This local endpoint can move an item through drafting/preparation only.
    # Verified status is intentionally reserved for a future authenticated review workflow.
    coverage.status = payload.status
    coverage.reviewer_note = payload.reviewer_note
    db.commit()
    return {"id": str(coverage.id), "status": coverage.status, "verified": False}


@router.post("/modules/{module_code}/competencies", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf), Depends(require_permission("platform:admin"))])
def create_competency(module_code: str, payload: CompetencyCreate, db: Session = Depends(get_db)) -> dict:
    module = _module_or_404(db, module_code)
    if db.scalar(select(Competency).where(Competency.code == payload.code)):
        raise HTTPException(status_code=409, detail="Já existe uma competência com esse código.")
    if payload.topic_id:
        topic = db.get(CurriculumTopic, payload.topic_id)
        if topic is None or topic.module_id != module.id:
            raise HTTPException(status_code=422, detail="O tópico selecionado não pertence ao módulo.")
    prerequisites = []
    if payload.prerequisite_ids:
        prerequisite_ids = list(dict.fromkeys(payload.prerequisite_ids))
        if len(prerequisite_ids) != len(payload.prerequisite_ids):
            raise HTTPException(status_code=422, detail="A lista de pré-requisitos contém identificadores duplicados.")
        prerequisites = list(db.scalars(select(Competency).where(Competency.id.in_(prerequisite_ids))))
        if len(prerequisites) != len(prerequisite_ids):
            raise HTTPException(status_code=422, detail="Um ou mais pré-requisitos não existem.")
    competency = Competency(
        module_id=module.id, topic_id=payload.topic_id, code=payload.code,
        title=payload.title, description=payload.description,
        is_security_relevant=payload.is_security_relevant,
        learning_requirements=[x[0] for x in LEARNING_REQUIREMENTS],
        internship_requirements=[x[0] for x in INTERNSHIP_REQUIREMENTS],
    )
    db.add(competency)
    _mark_module_as_draft(module)
    db.flush()
    if prerequisites:
        db.execute(insert(competency_prerequisites), [
            {"competency_id": competency.id, "prerequisite_id": item.id} for item in prerequisites
        ])
    for code, title in LEARNING_REQUIREMENTS:
        db.add(CoverageRequirement(competency_id=competency.id, center="learning", requirement_code=code, title=title, status="missing"))
    for code, title in INTERNSHIP_REQUIREMENTS:
        db.add(CoverageRequirement(competency_id=competency.id, center="internship", requirement_code=code, title=title, status="missing"))
    db.commit()
    return {"id": str(competency.id), "code": competency.code, "title": competency.title, "prerequisites_mapped": len(prerequisites), "coverage_items_created": len(LEARNING_REQUIREMENTS) + len(INTERNSHIP_REQUIREMENTS)}


@router.post("/modules/{module_code}/lessons", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf), Depends(require_permission("platform:admin"))])
def create_lesson(module_code: str, payload: LessonCreate, db: Session = Depends(get_db)) -> dict:
    module = _module_or_404(db, module_code)
    mapped = _ensure_competencies_belong_to_module(db, module.id, payload.competency_ids)
    if db.scalar(select(Lesson).where(Lesson.module_id == module.id, Lesson.code == payload.code)):
        raise HTTPException(status_code=409, detail="Já existe uma aula com esse código neste módulo.")
    lesson = Lesson(module_id=module.id, code=payload.code, title=payload.title, sequence=payload.sequence, summary=payload.summary, content_markdown=payload.content_markdown, status=payload.status)
    db.add(lesson)
    _mark_module_as_draft(module)
    db.flush()
    if mapped:
        db.execute(insert(lesson_competencies), [{"lesson_id": lesson.id, "competency_id": c.id} for c in mapped])
    db.commit()
    return {"id": str(lesson.id), "code": lesson.code, "title": lesson.title, "competencies_mapped": len(mapped)}


@router.post("/modules/{module_code}/labs", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf), Depends(require_permission("platform:admin"))])
def create_lab(module_code: str, payload: LabCreate, db: Session = Depends(get_db)) -> dict:
    module = _module_or_404(db, module_code)
    mapped = _ensure_competencies_belong_to_module(db, module.id, payload.competency_ids)
    if payload.safety_profile not in {"local-safe", "isolated-vm"}:
        raise HTTPException(status_code=422, detail="Por enquanto só são permitidos laboratórios locais seguros ou VMs isoladas descartáveis. A execução AWS exige um sandbox dedicado e ainda não está ligada ao motor de laboratórios.")
    if db.scalar(select(Lab).where(Lab.code == payload.code)):
        raise HTTPException(status_code=409, detail="Já existe um laboratório com esse código.")
    lab = Lab(module_id=module.id, code=payload.code, title=payload.title, description=payload.description, environment=payload.environment, safety_profile=payload.safety_profile, estimated_minutes=payload.estimated_minutes, manifest=payload.manifest, status="planned")
    db.add(lab)
    _mark_module_as_draft(module)
    db.flush()
    if mapped:
        db.execute(insert(lab_competencies), [{"lab_id": lab.id, "competency_id": c.id} for c in mapped])
    db.commit()
    return {"id": str(lab.id), "code": lab.code, "title": lab.title, "competencies_mapped": len(mapped), "safety_profile": lab.safety_profile}


@router.post("/modules/{module_code}/tickets", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf), Depends(require_permission("platform:admin"))])
def create_ticket(module_code: str, payload: TicketCreate, db: Session = Depends(get_db)) -> dict:
    module = _module_or_404(db, module_code)
    mapped = _ensure_competencies_belong_to_module(db, module.id, payload.competency_ids)
    if db.scalar(select(InternshipTicket).where(InternshipTicket.ticket_key == payload.ticket_key)):
        raise HTTPException(status_code=409, detail="Já existe um ticket com essa chave.")
    ticket = InternshipTicket(
        module_id=module.id, ticket_key=payload.ticket_key, title=payload.title,
        department=payload.department, priority=payload.priority, description=payload.description,
        business_impact=payload.business_impact, asset_context=payload.asset_context,
        assigned_role=payload.assigned_role, initial_state=payload.initial_state,
        investigation_steps=payload.investigation_steps, execution_steps=payload.execution_steps,
        validation_steps=payload.validation_steps, safety_scope=payload.safety_scope,
        acceptance_criteria=payload.acceptance_criteria,
    )
    db.add(ticket)
    _mark_module_as_draft(module)
    db.flush()
    if mapped:
        db.execute(insert(ticket_competencies), [{"ticket_id": ticket.id, "competency_id": c.id} for c in mapped])
    db.commit()
    return {"id": str(ticket.id), "ticket_key": ticket.ticket_key, "title": ticket.title, "competencies_mapped": len(mapped)}


@router.post("/modules/{module_code}/assessments", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf), Depends(require_permission("platform:admin"))])
def create_assessment(module_code: str, payload: AssessmentCreate, db: Session = Depends(get_db)) -> dict:
    module = _module_or_404(db, module_code)
    mapped = _ensure_competencies_belong_to_module(db, module.id, payload.competency_ids)
    if db.scalar(select(Assessment).where(Assessment.code == payload.code)):
        raise HTTPException(status_code=409, detail="Já existe uma avaliação com esse código.")
    assessment = Assessment(
        module_id=module.id, code=payload.code, title=payload.title,
        assessment_type=payload.assessment_type, total_points=payload.total_points,
        mastery_threshold=payload.mastery_threshold, rubric=payload.rubric, status="planned",
    )
    db.add(assessment)
    _mark_module_as_draft(module)
    db.flush()
    if mapped:
        db.execute(insert(assessment_competencies), [{"assessment_id": assessment.id, "competency_id": c.id} for c in mapped])
    db.commit()
    return {"id": str(assessment.id), "code": assessment.code, "title": assessment.title, "competencies_mapped": len(mapped)}


@router.post(
    "/assessments/{assessment_id}/attempts",
    status_code=status.HTTP_410_GONE,
    dependencies=[Depends(require_csrf), Depends(require_permission("assessments:attempt"))],
)
def create_assessment_attempt_legacy(assessment_id: UUID) -> dict:
    """Retired legacy route: assessment scores must only be assigned by a Reviewer."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Este endpoint foi substituído por /api/v1/learning/assessments/{assessment_id}/attempts. A nota só pode ser atribuída por um Reviewer.",
    )


@router.post(
    "/evidence",
    status_code=status.HTTP_410_GONE,
    dependencies=[Depends(require_csrf), Depends(require_permission("portfolio:manage"))],
)
def create_evidence_legacy() -> dict:
    """Retired legacy route: evidence must use the per-user review workflow."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Este endpoint foi substituído por /api/v1/learning/evidence, que associa a evidência ao utilizador autenticado e exige revisão.",
    )

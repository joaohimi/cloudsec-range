"""Idempotently author Linux L1 / M1 content into the Curriculum Engine.

The importer is additive: it creates missing records and associations, but it
never deletes records or overwrites existing authored content. Content changes
must be reviewed and applied through a versioned migration/content release.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import insert, select

from app.db.session import get_session_factory
from app.models import (
    Assessment,
    Competency,
    CoverageRequirement,
    CurriculumModule,
    CurriculumTopic,
    Lab,
    LearningResource,
    Lesson,
    InternshipTicket,
)
from app.models.curriculum import (
    assessment_competencies,
    competency_prerequisites,
    lab_competencies,
    lesson_competencies,
    ticket_competencies,
)

_SOURCE_PARENTS = Path(__file__).resolve().parents
_SOURCE_ROOT = _SOURCE_PARENTS[4] if len(_SOURCE_PARENTS) > 4 else Path("/app")
CONTENT_CANDIDATES = [
    Path("/workspace-content/curriculum/linux-l1-m01/module.json"),
    Path("/app/content/curriculum/linux-l1-m01/module.json"),
    Path.cwd() / "content" / "curriculum" / "linux-l1-m01" / "module.json",
    _SOURCE_ROOT / "content" / "curriculum" / "linux-l1-m01" / "module.json",
]
MANIFEST = next((path for path in CONTENT_CANDIDATES if path.is_file()), CONTENT_CANDIDATES[0])

LEARNING_REQUIREMENTS = {
    "definition": "Definição, finalidade e contexto",
    "prerequisites": "Pré-requisitos e dependências",
    "terminology": "Terminologia técnica explicada",
    "internal_behaviour": "Funcionamento interno e mecanismos",
    "standards_protocols": "Normas, padrões e protocolos relevantes",
    "official_documentation": "Documentação oficial e versão",
    "practical_examples": "Exemplos práticos",
    "guided_lab": "Laboratório guiado",
    "independent_exercise": "Exercício individual",
    "troubleshooting": "Cenário de troubleshooting",
    "security_context": "Relevância de segurança e controlos aplicáveis",
    "theory_assessment": "Avaliação teórica",
    "practical_assessment": "Avaliação prática",
    "evidence": "Evidência verificável de competência",
}

INTERNSHIP_REQUIREMENTS = {
    "company_context": "Contexto da empresa e do serviço",
    "responsible_role": "Função e responsabilidade profissional",
    "affected_assets": "Ativos e sistemas afetados",
    "ticket_request": "Ticket, pedido, incidente ou mudança",
    "initial_state": "Estado inicial reproduzível",
    "investigation": "Investigação e recolha de evidências",
    "execution": "Procedimento de execução ou correção",
    "validation": "Validação técnica",
    "acceptance_criteria": "Critérios de aceitação mensuráveis",
    "technical_review": "Revisão técnica",
    "documentation": "Documentação profissional",
    "evidence": "Evidência associada à competência",
}


def _content_root() -> Path:
    return MANIFEST.parent


def _load() -> dict[str, Any]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Versão do schema do conteúdo não suportada.")
    return payload


def _add_associations(db, table, left_column: str, left_id, competency_ids: list) -> int:
    inserted = 0
    for competency_id in competency_ids:
        exists = db.execute(
            select(table.c[left_column]).where(
                table.c[left_column] == left_id,
                table.c.competency_id == competency_id,
            )
        ).first()
        if not exists:
            db.execute(
                insert(table).values(**{left_column: left_id, "competency_id": competency_id})
            )
            inserted += 1
    return inserted


def seed() -> dict[str, int | str]:
    payload = _load()
    Session = get_session_factory()
    created = {
        "module": payload["module_code"],
        "topics": 0,
        "competencies": 0,
        "lessons": 0,
        "resources": 0,
        "labs": 0,
        "tickets": 0,
        "assessments": 0,
        "coverage_requirements": 0,
        "associations": 0,
    }

    with Session.begin() as db:
        module = db.scalar(
            select(CurriculumModule).where(CurriculumModule.code == payload["module_code"])
        )
        if module is None:
            raise RuntimeError(
                f"Módulo {payload['module_code']} não existe. Executa primeiro o importador do mapa canónico."
            )
        if module.source_module_code != payload["source_module_code"] or module.title != payload["module_title"]:
            raise RuntimeError("O módulo alvo não corresponde à fonte curricular canónica; importação cancelada.")

        topic_rows: dict[str, CurriculumTopic] = {}
        for item in payload["topics"]:
            row = db.scalar(
                select(CurriculumTopic).where(
                    CurriculumTopic.module_id == module.id,
                    CurriculumTopic.code == item["code"],
                )
            )
            if row is None:
                row = CurriculumTopic(module_id=module.id, **item)
                db.add(row)
                db.flush()
                created["topics"] += 1
            topic_rows[item["code"]] = row

        competency_rows: dict[str, Competency] = {}
        for item in payload["competencies"]:
            row = db.scalar(select(Competency).where(Competency.code == item["code"]))
            if row is None:
                row = Competency(
                    module_id=module.id,
                    topic_id=topic_rows[item["topic_code"]].id,
                    code=item["code"],
                    title=item["title"],
                    description=item["description"],
                    learning_requirements=item["learning_requirements"],
                    internship_requirements=item["internship_requirements"],
                    is_security_relevant=item["is_security_relevant"],
                )
                db.add(row)
                db.flush()
                created["competencies"] += 1
                for code, title in LEARNING_REQUIREMENTS.items():
                    status = "missing" if code == "evidence" else "draft"
                    db.add(CoverageRequirement(
                        competency_id=row.id, center="learning", requirement_code=code,
                        title=title, is_required=True, status=status,
                    ))
                    created["coverage_requirements"] += 1
                for code, title in INTERNSHIP_REQUIREMENTS.items():
                    status = "missing" if code == "evidence" else "draft"
                    db.add(CoverageRequirement(
                        competency_id=row.id, center="internship", requirement_code=code,
                        title=title, is_required=True, status=status,
                    ))
                    created["coverage_requirements"] += 1
            competency_rows[item["code"]] = row

        # Prerequisite edges are created only after every competency exists.
        for item in payload["competencies"]:
            current = competency_rows[item["code"]]
            for prereq_code in item["prerequisite_codes"]:
                prerequisite = competency_rows[prereq_code]
                exists = db.execute(
                    select(competency_prerequisites.c.competency_id).where(
                        competency_prerequisites.c.competency_id == current.id,
                        competency_prerequisites.c.prerequisite_id == prerequisite.id,
                    )
                ).first()
                if not exists:
                    db.execute(insert(competency_prerequisites).values(
                        competency_id=current.id, prerequisite_id=prerequisite.id
                    ))
                    created["associations"] += 1

        lesson_rows: dict[str, Lesson] = {}
        for item in payload["lessons"]:
            lesson = db.scalar(select(Lesson).where(Lesson.module_id == module.id, Lesson.code == item["code"]))
            if lesson is None:
                content = (_content_root() / item["file"]).read_text(encoding="utf-8")
                lesson = Lesson(
                    module_id=module.id,
                    code=item["code"],
                    title=item["title"],
                    sequence=item["sequence"],
                    summary=item["summary"],
                    content_markdown=content,
                    status="draft",
                )
                db.add(lesson)
                db.flush()
                created["lessons"] += 1
            lesson_rows[item["code"]] = lesson
            created["associations"] += _add_associations(
                db, lesson_competencies, "lesson_id", lesson.id,
                [competency_rows[code].id for code in item["competency_codes"]],
            )

        for item in payload["resources"]:
            resource = db.scalar(
                select(LearningResource).where(
                    LearningResource.module_id == module.id,
                    LearningResource.url == item["url"],
                )
            )
            if resource is None:
                competency_code = item["competency_codes"][0] if item["competency_codes"] else None
                resource = LearningResource(
                    module_id=module.id,
                    competency_id=competency_rows[competency_code].id if competency_code else None,
                    resource_type=item["resource_type"], title=item["title"], url=item["url"],
                    publisher=item["publisher"], product_version=item["product_version"],
                )
                db.add(resource)
                created["resources"] += 1

        lab_rows: dict[str, Lab] = {}
        for item in payload["labs"]:
            lab = db.scalar(select(Lab).where(Lab.code == item["code"]))
            if lab is None:
                lab = Lab(
                    module_id=module.id, code=item["code"], title=item["title"],
                    description=item["description"], environment="WSL2 Ubuntu 24.04",
                    safety_profile="local-safe", estimated_minutes=item["minutes"],
                    manifest=item["manifest"], status="planned",
                )
                db.add(lab)
                db.flush()
                created["labs"] += 1
            lab_rows[item["code"]] = lab
            created["associations"] += _add_associations(
                db, lab_competencies, "lab_id", lab.id,
                [competency_rows[code].id for code in item["competency_codes"]],
            )

        ticket_data = payload["ticket"]
        ticket = db.scalar(
            select(InternshipTicket).where(InternshipTicket.ticket_key == ticket_data["ticket_key"])
        )
        if ticket is None:
            ticket = InternshipTicket(
                module_id=module.id,
                ticket_key=ticket_data["ticket_key"],
                title=ticket_data["title"],
                department=ticket_data["department"],
                priority=ticket_data["priority"],
                status="backlog",
                description=ticket_data["description"],
                business_impact=ticket_data["business_impact"],
                asset_context=ticket_data["asset_context"],
                assigned_role=ticket_data["assigned_role"],
                initial_state=ticket_data["initial_state"],
                investigation_steps=ticket_data["investigation_steps"],
                execution_steps=ticket_data["execution_steps"],
                validation_steps=ticket_data["validation_steps"],
                safety_scope=ticket_data["safety_scope"],
                acceptance_criteria=ticket_data["acceptance_criteria"],
            )
            db.add(ticket)
            db.flush()
            created["tickets"] += 1
        created["associations"] += _add_associations(
            db, ticket_competencies, "ticket_id", ticket.id,
            [competency_rows[code].id for code in ticket_data["competency_codes"]],
        )

        assessment_data = payload["assessment"]
        assessment = db.scalar(
            select(Assessment).where(Assessment.code == assessment_data["code"])
        )
        if assessment is None:
            assessment = Assessment(
                module_id=module.id,
                code=assessment_data["code"],
                title=assessment_data["title"],
                assessment_type=assessment_data["assessment_type"],
                total_points=assessment_data["total_points"],
                mastery_threshold=assessment_data["mastery_threshold"],
                rubric=assessment_data["rubric"],
                status="planned",
            )
            db.add(assessment)
            db.flush()
            created["assessments"] += 1
        created["associations"] += _add_associations(
            db, assessment_competencies, "assessment_id", assessment.id,
            [competency_rows[code].id for code in assessment_data["competency_codes"]],
        )

        if module.content_status == "not_authored":
            module.content_status = "draft"

    return created


if __name__ == "__main__":
    print(json.dumps(seed(), ensure_ascii=False, indent=2))

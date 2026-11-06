"""Curriculum Engine: versioned roadmap, lessons, labs, tickets, assessments and evidence.

Revision ID: 0002_curriculum_engine
Revises: 0001_initial
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_curriculum_engine"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = sa.Uuid()
NOW = sa.func.now()


def timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    ]


def upgrade() -> None:
    op.create_table(
        "curriculum_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("source_filename", sa.String(500), nullable=False),
        sa.Column("source_checksum", sa.String(128)),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("import_notes", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_curriculum_versions_code", "curriculum_versions", ["code"], unique=True)

    op.add_column("curriculum_tracks", sa.Column("version_id", UUID, nullable=True))
    op.create_foreign_key(
        "fk_curriculum_tracks_version_id", "curriculum_tracks", "curriculum_versions",
        ["version_id"], ["id"], ondelete="SET NULL",
    )

    op.create_table(
        "curriculum_blocks",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("track_id", UUID, sa.ForeignKey("curriculum_tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("track_id", "code", name="uq_curriculum_block_track_code"),
    )
    op.create_index("ix_curriculum_blocks_track_id", "curriculum_blocks", ["track_id"])

    op.add_column("curriculum_modules", sa.Column("block_id", UUID, nullable=True))
    op.add_column("curriculum_modules", sa.Column("source_module_code", sa.String(40), nullable=True))
    op.add_column("curriculum_modules", sa.Column("estimated_hours", sa.Integer(), nullable=True))
    op.add_column(
        "curriculum_modules",
        sa.Column("content_status", sa.String(30), nullable=False, server_default="not_authored"),
    )
    op.create_foreign_key(
        "fk_curriculum_modules_block_id", "curriculum_modules", "curriculum_blocks",
        ["block_id"], ["id"], ondelete="SET NULL",
    )

    op.create_table(
        "curriculum_topics",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("module_id", UUID, sa.ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text()),
        *timestamps(),
        sa.UniqueConstraint("module_id", "code", name="uq_curriculum_topic_module_code"),
    )
    op.create_index("ix_curriculum_topics_module_id", "curriculum_topics", ["module_id"])

    op.add_column("competencies", sa.Column("topic_id", UUID, nullable=True))
    op.create_foreign_key(
        "fk_competencies_topic_id", "competencies", "curriculum_topics",
        ["topic_id"], ["id"], ondelete="SET NULL",
    )

    op.create_table(
        "lessons",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("module_id", UUID, sa.ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("content_markdown", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_authored"),
        sa.Column("official_sources_reviewed_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.UniqueConstraint("module_id", "code", name="uq_lesson_module_code"),
    )
    op.create_index("ix_lessons_module_id", "lessons", ["module_id"])

    op.create_table(
        "labs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("module_id", UUID, sa.ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=True),
        sa.Column("track_id", UUID, sa.ForeignKey("curriculum_tracks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("environment", sa.String(120), nullable=False, server_default="WSL2 Ubuntu 24.04"),
        sa.Column("safety_profile", sa.String(50), nullable=False, server_default="local-safe"),
        sa.Column("estimated_minutes", sa.Integer()),
        sa.Column("manifest", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(30), nullable=False, server_default="planned"),
        *timestamps(),
        sa.CheckConstraint("module_id IS NOT NULL OR track_id IS NOT NULL", name="ck_lab_has_track_or_module"),
    )
    op.create_index("ix_labs_module_id", "labs", ["module_id"])
    op.create_index("ix_labs_track_id", "labs", ["track_id"])
    op.create_index("ix_labs_code", "labs", ["code"], unique=True)

    op.create_table(
        "assessments",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("module_id", UUID, sa.ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("assessment_type", sa.String(40), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("mastery_threshold", sa.Float(), nullable=False, server_default="80"),
        sa.Column("rubric", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(30), nullable=False, server_default="planned"),
        *timestamps(),
    )
    op.create_index("ix_assessments_module_id", "assessments", ["module_id"])
    op.create_index("ix_assessments_code", "assessments", ["code"], unique=True)

    op.create_table(
        "lesson_competencies",
        sa.Column("lesson_id", UUID, sa.ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("competency_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "lab_competencies",
        sa.Column("lab_id", UUID, sa.ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("competency_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "assessment_competencies",
        sa.Column("assessment_id", UUID, sa.ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("competency_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "ticket_competencies",
        sa.Column("ticket_id", UUID, sa.ForeignKey("internship_tickets.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("competency_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "competency_prerequisites",
        sa.Column("competency_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("prerequisite_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
        sa.CheckConstraint("competency_id <> prerequisite_id", name="ck_competency_not_own_prerequisite"),
    )

    op.add_column("internship_tickets", sa.Column("module_id", UUID, nullable=True))
    op.add_column("internship_tickets", sa.Column("asset_context", sa.Text(), nullable=True))
    op.add_column("internship_tickets", sa.Column("assigned_role", sa.String(120), nullable=True))
    op.add_column("internship_tickets", sa.Column("initial_state", sa.Text(), nullable=True))
    op.add_column("internship_tickets", sa.Column("investigation_steps", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("internship_tickets", sa.Column("execution_steps", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("internship_tickets", sa.Column("validation_steps", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("internship_tickets", sa.Column("safety_scope", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_internship_tickets_module_id", "internship_tickets", "curriculum_modules",
        ["module_id"], ["id"], ondelete="SET NULL",
    )

    op.create_table(
        "assessment_attempts",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("assessment_id", UUID, sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learner_key", sa.String(80), nullable=False, server_default="primary"),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("answers", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("feedback", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        *timestamps(),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_assessment_attempt_score_range"),
    )
    op.create_index("ix_assessment_attempts_assessment_id", "assessment_attempts", ["assessment_id"])

    op.create_table(
        "coverage_requirements",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("competency_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("center", sa.String(20), nullable=False),
        sa.Column("requirement_code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(30), nullable=False, server_default="missing"),
        sa.Column("reviewer_note", sa.Text()),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.UniqueConstraint("competency_id", "center", "requirement_code", name="uq_coverage_requirement_key"),
        sa.CheckConstraint("center IN ('learning', 'internship')", name="ck_coverage_center"),
        sa.CheckConstraint("status IN ('missing', 'draft', 'ready', 'verified', 'not_applicable')", name="ck_coverage_status"),
    )
    op.create_index("ix_coverage_requirements_competency_id", "coverage_requirements", ["competency_id"])

    op.create_table(
        "competency_progress",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("competency_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learner_key", sa.String(80), nullable=False, server_default="primary"),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("mastery_score", sa.Float()),
        sa.Column("notes", sa.Text()),
        sa.Column("last_assessed_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.UniqueConstraint("competency_id", "learner_key", name="uq_competency_progress_learner"),
        sa.CheckConstraint("mastery_score IS NULL OR (mastery_score >= 0 AND mastery_score <= 100)", name="ck_mastery_score_range"),
    )
    op.create_index("ix_competency_progress_competency_id", "competency_progress", ["competency_id"])

    op.create_table(
        "evidence",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("competency_id", UUID, sa.ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", UUID, sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lab_id", UUID, sa.ForeignKey("labs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ticket_id", UUID, sa.ForeignKey("internship_tickets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assessment_attempt_id", UUID, sa.ForeignKey("assessment_attempts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("artifact_uri", sa.String(1000)),
        sa.Column("summary", sa.Text()),
        sa.Column("sanitized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("review_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("metadata_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        *timestamps(),
        sa.CheckConstraint(
            "lesson_id IS NOT NULL OR lab_id IS NOT NULL OR ticket_id IS NOT NULL OR assessment_attempt_id IS NOT NULL",
            name="ck_evidence_has_source",
        ),
    )
    op.create_index("ix_evidence_competency_id", "evidence", ["competency_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_competency_id", table_name="evidence")
    op.drop_table("evidence")
    op.drop_index("ix_competency_progress_competency_id", table_name="competency_progress")
    op.drop_table("competency_progress")
    op.drop_index("ix_coverage_requirements_competency_id", table_name="coverage_requirements")
    op.drop_table("coverage_requirements")
    op.drop_index("ix_assessment_attempts_assessment_id", table_name="assessment_attempts")
    op.drop_table("assessment_attempts")

    op.drop_constraint("fk_internship_tickets_module_id", "internship_tickets", type_="foreignkey")
    for column in ["safety_scope", "validation_steps", "execution_steps", "investigation_steps", "initial_state", "assigned_role", "asset_context", "module_id"]:
        op.drop_column("internship_tickets", column)

    op.drop_table("competency_prerequisites")
    op.drop_table("ticket_competencies")
    op.drop_table("assessment_competencies")
    op.drop_table("lab_competencies")
    op.drop_table("lesson_competencies")
    op.drop_index("ix_assessments_code", table_name="assessments")
    op.drop_index("ix_assessments_module_id", table_name="assessments")
    op.drop_table("assessments")
    op.drop_index("ix_labs_code", table_name="labs")
    op.drop_index("ix_labs_track_id", table_name="labs")
    op.drop_index("ix_labs_module_id", table_name="labs")
    op.drop_table("labs")
    op.drop_index("ix_lessons_module_id", table_name="lessons")
    op.drop_table("lessons")

    op.drop_constraint("fk_competencies_topic_id", "competencies", type_="foreignkey")
    op.drop_column("competencies", "topic_id")
    op.drop_index("ix_curriculum_topics_module_id", table_name="curriculum_topics")
    op.drop_table("curriculum_topics")

    op.drop_constraint("fk_curriculum_modules_block_id", "curriculum_modules", type_="foreignkey")
    for column in ["content_status", "estimated_hours", "source_module_code", "block_id"]:
        op.drop_column("curriculum_modules", column)
    op.drop_index("ix_curriculum_blocks_track_id", table_name="curriculum_blocks")
    op.drop_table("curriculum_blocks")
    op.drop_constraint("fk_curriculum_tracks_version_id", "curriculum_tracks", type_="foreignkey")
    op.drop_column("curriculum_tracks", "version_id")
    op.drop_index("ix_curriculum_versions_code", table_name="curriculum_versions")
    op.drop_table("curriculum_versions")

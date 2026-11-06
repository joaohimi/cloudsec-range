"""M2: user management and per-user learning progress.

Revision ID: 0004_learning_progress
Revises: 0003_platform_core
Create Date: 2026-11-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_learning_progress"
down_revision: Union[str, None] = "0003_platform_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = sa.Uuid()
JSONB = postgresql.JSONB(astext_type=sa.Text())
NOW = sa.func.now()


def timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    ]


def upgrade() -> None:
    # Enforce case-insensitive email uniqueness as accounts are created through
    # administrative workflows. Existing duplicate normalized emails must be
    # resolved before this migration; the current bootstrap account is unique.
    op.execute("CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email))")

    # Attach existing progress/evidence records to real user identities when
    # explicitly created after this migration. Legacy learner_key rows remain
    # intact and intentionally unassigned; no historical ownership is guessed.
    op.add_column("competency_progress", sa.Column("user_id", UUID, nullable=True))
    op.add_column("competency_progress", sa.Column("self_assessment_notes", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_competency_progress_user_id", "competency_progress", "users",
        ["user_id"], ["id"], ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_competency_progress_user_competency", "competency_progress", ["user_id", "competency_id"]
    )
    op.create_index("ix_competency_progress_user_id", "competency_progress", ["user_id"])

    op.add_column("assessment_attempts", sa.Column("user_id", UUID, nullable=True))
    op.add_column("assessment_attempts", sa.Column("review_status", sa.String(30), nullable=False, server_default="reviewed"))
    op.add_column("assessment_attempts", sa.Column("reviewed_by_user_id", UUID, nullable=True))
    op.add_column("assessment_attempts", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_assessment_attempts_user_id", "assessment_attempts", "users",
        ["user_id"], ["id"], ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_assessment_attempts_reviewed_by_user_id", "assessment_attempts", "users",
        ["reviewed_by_user_id"], ["id"], ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_assessment_attempt_review_status", "assessment_attempts",
        "review_status IN ('submitted', 'in_review', 'reviewed', 'returned')",
    )
    op.create_index("ix_assessment_attempts_user_assessment", "assessment_attempts", ["user_id", "assessment_id", "submitted_at"])

    op.add_column("evidence", sa.Column("user_id", UUID, nullable=True))
    op.add_column("evidence", sa.Column("reviewed_by_user_id", UUID, nullable=True))
    op.add_column("evidence", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_evidence_user_id", "evidence", "users", ["user_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_evidence_reviewed_by_user_id", "evidence", "users",
        ["reviewed_by_user_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_evidence_user_created", "evidence", ["user_id", "created_at"])

    op.create_table(
        "lesson_progress",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", UUID, sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="in_progress"),
        sa.Column("completion_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_position", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),
        sa.CheckConstraint("status IN ('in_progress', 'completed')", name="ck_lesson_progress_status"),
        sa.CheckConstraint("completion_percent >= 0 AND completion_percent <= 100", name="ck_lesson_progress_percent"),
        sa.CheckConstraint("time_spent_seconds >= 0", name="ck_lesson_progress_time"),
    )
    op.create_index("ix_lesson_progress_user_status", "lesson_progress", ["user_id", "status"])

    op.create_table(
        "lab_attempts",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lab_id", UUID, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="started"),
        sa.Column("learner_notes", sa.Text()),
        sa.Column("submission", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("validation_report", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by_user_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.CheckConstraint(
            "status IN ('started', 'submitted', 'in_review', 'validated', 'failed', 'returned', 'aborted')",
            name="ck_lab_attempt_status",
        ),
    )
    op.create_index("ix_lab_attempts_user_lab_created", "lab_attempts", ["user_id", "lab_id", "created_at"])
    op.create_index("ix_lab_attempts_status", "lab_attempts", ["status"])

    # Add a dedicated permission rather than making every reviewer an owner.
    op.execute(sa.text(
        "INSERT INTO permissions (id, code, name, description) "
        "VALUES (gen_random_uuid(), 'labs:review', 'Rever laboratórios', "
        "'Validar ou devolver submissões de laboratórios.') "
        "ON CONFLICT (code) DO NOTHING"
    ))
    op.execute(sa.text(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
        "WHERE r.code IN ('owner', 'reviewer') AND p.code = 'labs:review' "
        "ON CONFLICT DO NOTHING"
    ))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code='labs:review')"))
    op.execute(sa.text("DELETE FROM permissions WHERE code='labs:review'"))
    op.drop_index("ix_lab_attempts_status", table_name="lab_attempts")
    op.drop_index("ix_lab_attempts_user_lab_created", table_name="lab_attempts")
    op.drop_table("lab_attempts")
    op.drop_index("ix_lesson_progress_user_status", table_name="lesson_progress")
    op.drop_table("lesson_progress")
    op.drop_index("ix_evidence_user_created", table_name="evidence")
    op.drop_constraint("fk_evidence_reviewed_by_user_id", "evidence", type_="foreignkey")
    op.drop_constraint("fk_evidence_user_id", "evidence", type_="foreignkey")
    op.drop_column("evidence", "reviewed_at")
    op.drop_column("evidence", "reviewed_by_user_id")
    op.drop_column("evidence", "user_id")
    op.drop_index("ix_assessment_attempts_user_assessment", table_name="assessment_attempts")
    op.drop_constraint("ck_assessment_attempt_review_status", "assessment_attempts", type_="check")
    op.drop_constraint("fk_assessment_attempts_reviewed_by_user_id", "assessment_attempts", type_="foreignkey")
    op.drop_constraint("fk_assessment_attempts_user_id", "assessment_attempts", type_="foreignkey")
    op.drop_column("assessment_attempts", "reviewed_at")
    op.drop_column("assessment_attempts", "reviewed_by_user_id")
    op.drop_column("assessment_attempts", "review_status")
    op.drop_column("assessment_attempts", "user_id")
    op.drop_index("ix_competency_progress_user_id", table_name="competency_progress")
    op.drop_constraint("uq_competency_progress_user_competency", "competency_progress", type_="unique")
    op.drop_constraint("fk_competency_progress_user_id", "competency_progress", type_="foreignkey")
    op.drop_column("competency_progress", "self_assessment_notes")
    op.drop_column("competency_progress", "user_id")
    op.execute("DROP INDEX uq_users_email_lower")

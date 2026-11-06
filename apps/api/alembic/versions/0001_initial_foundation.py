"""Initial curriculum and internship foundation.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "curriculum_tracks",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_curriculum_tracks_code", "curriculum_tracks", ["code"], unique=True)

    op.create_table(
        "curriculum_modules",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("track_id", sa.Uuid(), sa.ForeignKey("curriculum_tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False, unique=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("canonical_source", sa.String(length=500), nullable=True),
        sa.Column("source_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_curriculum_modules_code", "curriculum_modules", ["code"], unique=True)

    op.create_table(
        "competencies",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("module_id", sa.Uuid(), sa.ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("learning_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("internship_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_security_relevant", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_competencies_code", "competencies", ["code"], unique=True)

    op.create_table(
        "learning_resources",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("module_id", sa.Uuid(), sa.ForeignKey("curriculum_modules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("competency_id", sa.Uuid(), sa.ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resource_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("publisher", sa.String(length=160), nullable=True),
        sa.Column("product_version", sa.String(length=80), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "internship_tickets",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("ticket_key", sa.String(length=40), nullable=False, unique=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="backlog"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("business_impact", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_internship_tickets_ticket_key", "internship_tickets", ["ticket_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_internship_tickets_ticket_key", table_name="internship_tickets")
    op.drop_table("internship_tickets")
    op.drop_table("learning_resources")
    op.drop_index("ix_competencies_code", table_name="competencies")
    op.drop_table("competencies")
    op.drop_index("ix_curriculum_modules_code", table_name="curriculum_modules")
    op.drop_table("curriculum_modules")
    op.drop_index("ix_curriculum_tracks_code", table_name="curriculum_tracks")
    op.drop_table("curriculum_tracks")

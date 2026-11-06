from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Table, Column,
    Text, UniqueConstraint, Uuid, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


lesson_competencies = Table(
    "lesson_competencies", Base.metadata,
    Column("lesson_id", Uuid(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
    Column("competency_id", Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
)

lab_competencies = Table(
    "lab_competencies", Base.metadata,
    Column("lab_id", Uuid(as_uuid=True), ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
    Column("competency_id", Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
)

assessment_competencies = Table(
    "assessment_competencies", Base.metadata,
    Column("assessment_id", Uuid(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True),
    Column("competency_id", Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
)


ticket_competencies = Table(
    "ticket_competencies", Base.metadata,
    Column("ticket_id", Uuid(as_uuid=True), ForeignKey("internship_tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("competency_id", Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
)

competency_prerequisites = Table(
    "competency_prerequisites", Base.metadata,
    Column("competency_id", Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
    Column("prerequisite_id", Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True),
    CheckConstraint("competency_id <> prerequisite_id", name="ck_competency_not_own_prerequisite"),
)


class CurriculumVersion(TimestampMixin, Base):
    __tablename__ = "curriculum_versions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    source_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    source_checksum: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    import_notes: Mapped[str | None] = mapped_column(Text)


class CurriculumTrack(TimestampMixin, Base):
    __tablename__ = "curriculum_tracks"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    version_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_versions.id", ondelete="SET NULL")
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    modules: Mapped[list["CurriculumModule"]] = relationship(
        back_populates="track", cascade="all, delete-orphan", order_by="CurriculumModule.position"
    )
    blocks: Mapped[list["CurriculumBlock"]] = relationship(
        back_populates="track", cascade="all, delete-orphan", order_by="CurriculumBlock.position"
    )


class CurriculumBlock(TimestampMixin, Base):
    __tablename__ = "curriculum_blocks"
    __table_args__ = (UniqueConstraint("track_id", "code", name="uq_curriculum_block_track_code"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    track_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_tracks.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    track: Mapped[CurriculumTrack] = relationship(back_populates="blocks")


class CurriculumModule(TimestampMixin, Base):
    __tablename__ = "curriculum_modules"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    track_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_tracks.id", ondelete="CASCADE"), nullable=False
    )
    block_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_blocks.id", ondelete="SET NULL")
    )
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    source_module_code: Mapped[str | None] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_hours: Mapped[int | None] = mapped_column(Integer)
    content_status: Mapped[str] = mapped_column(String(30), default="not_authored", nullable=False)
    canonical_source: Mapped[str | None] = mapped_column(String(500))
    source_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    track: Mapped[CurriculumTrack] = relationship(back_populates="modules")
    competencies: Mapped[list["Competency"]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="Competency.code"
    )


class CurriculumTopic(TimestampMixin, Base):
    __tablename__ = "curriculum_topics"
    __table_args__ = (UniqueConstraint("module_id", "code", name="uq_curriculum_topic_module_code"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    module_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Competency(TimestampMixin, Base):
    __tablename__ = "competencies"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    module_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_topics.id", ondelete="SET NULL")
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    learning_requirements: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    internship_requirements: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    is_security_relevant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    module: Mapped[CurriculumModule] = relationship(back_populates="competencies")


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("module_id", "code", name="uq_lesson_module_code"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    module_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content_markdown: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="not_authored", nullable=False)
    official_sources_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Lab(TimestampMixin, Base):
    __tablename__ = "labs"
    __table_args__ = (CheckConstraint("module_id IS NOT NULL OR track_id IS NOT NULL", name="ck_lab_has_track_or_module"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    module_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_modules.id", ondelete="CASCADE")
    )
    track_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_tracks.id", ondelete="CASCADE")
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    environment: Mapped[str] = mapped_column(String(120), nullable=False, default="WSL2 Ubuntu 24.04")
    safety_profile: Mapped[str] = mapped_column(String(50), nullable=False, default="local-safe")
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    manifest: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)


class Assessment(TimestampMixin, Base):
    __tablename__ = "assessments"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    module_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(40), nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    mastery_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)
    rubric: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)


class AssessmentAttempt(TimestampMixin, Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_assessment_attempt_score_range"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    learner_key: Mapped[str] = mapped_column(String(80), nullable=False, default="primary")
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="reviewed", server_default="reviewed")
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answers: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    feedback: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CoverageRequirement(TimestampMixin, Base):
    __tablename__ = "coverage_requirements"
    __table_args__ = (
        UniqueConstraint("competency_id", "center", "requirement_code", name="uq_coverage_requirement_key"),
        CheckConstraint("center IN ('learning', 'internship')", name="ck_coverage_center"),
        CheckConstraint("status IN ('missing', 'draft', 'ready', 'verified', 'not_applicable')", name="ck_coverage_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    competency_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    center: Mapped[str] = mapped_column(String(20), nullable=False)
    requirement_code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="missing")
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompetencyProgress(TimestampMixin, Base):
    __tablename__ = "competency_progress"
    __table_args__ = (
        UniqueConstraint("competency_id", "learner_key", name="uq_competency_progress_learner"),
        CheckConstraint("mastery_score IS NULL OR (mastery_score >= 0 AND mastery_score <= 100)", name="ck_mastery_score_range"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    competency_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    learner_key: Mapped[str] = mapped_column(String(80), nullable=False, default="primary")
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_started")
    mastery_score: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    self_assessment_notes: Mapped[str | None] = mapped_column(Text)
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Evidence(TimestampMixin, Base):
    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint(
            "lesson_id IS NOT NULL OR lab_id IS NOT NULL OR ticket_id IS NOT NULL OR assessment_attempt_id IS NOT NULL",
            name="ck_evidence_has_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    competency_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lesson_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("lessons.id", ondelete="SET NULL"))
    lab_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("labs.id", ondelete="SET NULL"))
    ticket_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("internship_tickets.id", ondelete="SET NULL"))
    assessment_attempt_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="SET NULL"))
    evidence_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    artifact_uri: Mapped[str | None] = mapped_column(String(1000))
    summary: Mapped[str | None] = mapped_column(Text)
    sanitized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class LearningResource(TimestampMixin, Base):
    __tablename__ = "learning_resources"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    module_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_modules.id", ondelete="SET NULL")
    )
    competency_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("competencies.id", ondelete="SET NULL")
    )
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(160))
    product_version: Mapped[str | None] = mapped_column(String(80))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

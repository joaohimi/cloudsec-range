from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Float, Integer, String, Text, UniqueConstraint, Uuid, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class LessonProgress(TimestampMixin, Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),
        CheckConstraint("status IN ('in_progress', 'completed')", name="ck_lesson_progress_status"),
        CheckConstraint("completion_percent >= 0 AND completion_percent <= 100", name="ck_lesson_progress_percent"),
        CheckConstraint("time_spent_seconds >= 0", name="ck_lesson_progress_time"),
        Index("ix_lesson_progress_user_status", "user_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="in_progress")
    completion_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_position: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LabAttempt(TimestampMixin, Base):
    __tablename__ = "lab_attempts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('started', 'submitted', 'in_review', 'validated', 'failed', 'returned', 'aborted')",
            name="ck_lab_attempt_status",
        ),
        Index("ix_lab_attempts_user_lab_created", "user_id", "lab_id", "created_at"),
        Index("ix_lab_attempts_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lab_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="started")
    learner_notes: Mapped[str | None] = mapped_column(Text)
    submission: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    validation_report: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

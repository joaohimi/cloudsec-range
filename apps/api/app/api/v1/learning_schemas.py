from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LessonProgressUpdate(BaseModel):
    status: str = Field(pattern="^(in_progress|completed)$")
    completion_percent: float = Field(default=0, ge=0, le=100)
    time_spent_seconds: int = Field(default=0, ge=0, le=10_000_000)
    last_position: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class LabAttemptSubmit(BaseModel):
    learner_notes: str = Field(min_length=10, max_length=20_000)
    submission: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class LabAttemptReview(BaseModel):
    outcome: str = Field(pattern="^(validated|failed|returned)$")
    validation_report: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class AssessmentAttemptCreate(BaseModel):
    answers: dict = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class AssessmentAttemptReview(BaseModel):
    score: float = Field(ge=0, le=100)
    feedback: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class CompetencySelfAssessment(BaseModel):
    status: str = Field(pattern="^(in_progress|self_assessed)$")
    notes: str = Field(min_length=10, max_length=10_000)

    model_config = ConfigDict(extra="forbid")


class CompetencyReview(BaseModel):
    learner_user_id: UUID
    status: str = Field(pattern="^(demonstrated|mastered|requires_reinforcement)$")
    mastery_score: float | None = Field(default=None, ge=0, le=100)
    notes: str = Field(min_length=5, max_length=10_000)

    model_config = ConfigDict(extra="forbid")


class EvidenceCreate(BaseModel):
    competency_id: UUID
    lesson_id: UUID | None = None
    lab_id: UUID | None = None
    assessment_attempt_id: UUID | None = None
    evidence_type: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=3, max_length=240)
    artifact_uri: str | None = Field(default=None, max_length=1000)
    summary: str = Field(min_length=10, max_length=10_000)

    model_config = ConfigDict(extra="forbid")


class EvidenceReview(BaseModel):
    review_status: str = Field(pattern="^(accepted|rejected|needs_changes)$")
    review_note: str = Field(min_length=5, max_length=10_000)

    model_config = ConfigDict(extra="forbid")


class Message(BaseModel):
    message: str

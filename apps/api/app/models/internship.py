from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class InternshipTicket(TimestampMixin, Base):
    __tablename__ = "internship_tickets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    module_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("curriculum_modules.id", ondelete="SET NULL")
    )
    ticket_key: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="backlog", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    business_impact: Mapped[str | None] = mapped_column(Text)
    asset_context: Mapped[str | None] = mapped_column(Text)
    assigned_role: Mapped[str | None] = mapped_column(String(120))
    initial_state: Mapped[str | None] = mapped_column(Text)
    investigation_steps: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    execution_steps: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    validation_steps: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    safety_scope: Mapped[str | None] = mapped_column(Text)
    acceptance_criteria: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

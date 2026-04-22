from app.infrastructure.database.database import Base
from sqlalchemy import String, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.user import User
    from app.domain.models.job_document import JobDocument
    from app.domain.models.business_profile import BusinessProfile


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    html: Mapped[str] = mapped_column(String, nullable=False)
    # System Fields
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_profiles.id")
    )
    system_prompt_override: Mapped[str] = mapped_column(String, nullable=True)
    # Relationships
    business: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile", 
        back_populates="document_templates",
        foreign_keys=[business_id]
    )
    job_documents: Mapped[list["JobDocument"]] = relationship(
        "JobDocument", back_populates="document_template"
    )

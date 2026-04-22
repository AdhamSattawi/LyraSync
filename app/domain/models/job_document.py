from app.infrastructure.database.database import Base
from sqlalchemy import String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.domain.enums.job_document_status import JobDocumentStatus
from sqlalchemy import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.job import Job
    from app.domain.models.document_template import DocumentTemplate
    from app.domain.models.user import User


class JobDocument(Base):
    __tablename__ = "job_documents"

    document_url: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[JobDocumentStatus] = mapped_column(
        Enum(JobDocumentStatus), nullable=True
    )

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    document_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_templates.id")
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="job_documents")
    document_template: Mapped["DocumentTemplate"] = relationship(
        "DocumentTemplate", back_populates="job_documents"
    )
    created_by: Mapped["User"] = relationship("User", back_populates="job_documents")

from app.infrastructure.database.database import Base
from sqlalchemy import String, TIMESTAMP, ForeignKey, Integer, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.domain.enums.job_status import JobStatus
from sqlalchemy import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.business_profile import BusinessProfile
    from app.domain.models.client import Client
    from app.domain.models.job_document import JobDocument
    from app.domain.models.job_item import JobItem
    from app.domain.models.user import User
    from app.domain.models.transaction import Transaction


class Job(Base):
    __tablename__ = "jobs"

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    location: Mapped[str] = mapped_column(String, nullable=True)
    job_type: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), nullable=False)
    raw_data: Mapped[str] = mapped_column(String, nullable=False)
    parsed_data: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_profiles.id")
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id")
    )

    total_price: Mapped[int] = mapped_column(Integer, nullable=True)
    currency_code: Mapped[str] = mapped_column(String, nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    invoice_number: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    is_finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Relationships
    business: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile", back_populates="jobs"
    )
    client: Mapped["Client"] = relationship("Client", back_populates="jobs")
    job_documents: Mapped[list["JobDocument"]] = relationship(
        "JobDocument", back_populates="job"
    )
    items: Mapped[list["JobItem"]] = relationship(
        "JobItem", back_populates="job", cascade="all, delete-orphan"
    )
    created_by: Mapped["User"] = relationship("User", back_populates="jobs")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="job"
    )

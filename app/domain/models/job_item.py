from app.domain.models.business_profile import BusinessProfile
from app.infrastructure.database.database import Base
from sqlalchemy import String, Float, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.job import Job


class JobItem(Base):
    __tablename__ = "job_items"

    description: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="items")

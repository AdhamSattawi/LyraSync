from app.infrastructure.database.database import Base
from sqlalchemy import String, TIMESTAMP, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.job import Job
    from app.domain.models.business_profile import BusinessProfile


class Client(Base):
    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    phone_country_code: Mapped[str] = mapped_column(
        String, nullable=False, default="+972"
    )
    address: Mapped[str] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=True)
    country_code: Mapped[str] = mapped_column(String, nullable=True)
    tax_id: Mapped[str] = mapped_column(String, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_profiles.id")
    )
    # Relationships
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="client")
    business: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile", back_populates="clients"
    )

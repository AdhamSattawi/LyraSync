from app.infrastructure.database.database import Base
from sqlalchemy import String, TIMESTAMP, ForeignKey, Integer, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.domain.enums.transaction_type import TransactionType
from sqlalchemy import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.user import User
    from app.domain.models.business_profile import BusinessProfile
    from app.domain.models.job import Job


class Transaction(Base):
    __tablename__ = "transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_profiles.id")
    )
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_code: Mapped[str] = mapped_column(String, nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True
    )
    description: Mapped[str] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    receipt_url: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    business: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile", back_populates="transactions"
    )
    job: Mapped["Job"] = relationship("Job", back_populates="transactions")

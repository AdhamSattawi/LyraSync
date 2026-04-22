from app.infrastructure.database.database import Base
from sqlalchemy import String, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.domain.enums.user_role import UserRole
from sqlalchemy import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.business_profile import BusinessProfile
    from app.domain.models.conversation_state import ConversationState
    from app.domain.models.job_document import JobDocument
    from app.domain.models.job import Job
    from app.domain.models.transaction import Transaction
    from app.domain.models.message import Message


class User(Base):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone_country_code: Mapped[str] = mapped_column(
        String, nullable=False, default="+972"
    )
    language_preference: Mapped[str] = mapped_column(String, nullable=False, default="en")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_profiles.id")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    business: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile", back_populates="user"
    )
    conversation_states: Mapped[list["ConversationState"]] = relationship(
        "ConversationState", back_populates="user"
    )
    job_documents: Mapped[list["JobDocument"]] = relationship(
        "JobDocument", back_populates="created_by"
    )
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="created_by")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="user"
    )
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="user")

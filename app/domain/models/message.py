from app.infrastructure.database.database import Base
from sqlalchemy import String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import TYPE_CHECKING
import enum

if TYPE_CHECKING:
    from app.domain.models.user import User
    from app.domain.models.business_profile import BusinessProfile


class MessageDirection(enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class Message(Base):
    __tablename__ = "messages"

    from_phone: Mapped[str] = mapped_column(String, nullable=False)
    to_phone: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=True)
    media_url: Mapped[str] = mapped_column(String, nullable=True)
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection), nullable=False
    )
    platform: Mapped[str] = mapped_column(String, nullable=False, default="whatsapp")
    
    # Contextual links
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="messages")
    business: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile", back_populates="messages"
    )

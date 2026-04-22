from sqlalchemy import String, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import timedelta
from app.infrastructure.database.database import Base
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.user import User


class ConversationState(Base):
    __tablename__ = "conversation_states"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    active_intent: Mapped[str] = mapped_column(String, nullable=False)
    pending_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    expires_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.now() + timedelta(days=1)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversation_states")

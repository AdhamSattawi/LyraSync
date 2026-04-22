from app.domain.models.conversation_state import ConversationState
from app.domain.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid


class ConversationRepository:
    async def get_user_by_phone(
        self, session: AsyncSession, phone: str
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_active(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> ConversationState | None:
        result = await session.execute(
            select(ConversationState)
            .where(ConversationState.user_id == user_id)
            .where(ConversationState.expires_at > datetime.utcnow())
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, session: AsyncSession, user_id: uuid.UUID, intent: str, payload: dict
    ) -> ConversationState:
        existing = await self.get_active(session, user_id)
        if existing is not None:
            existing.active_intent = intent
            existing.pending_payload = payload
            existing.updated_at = datetime.utcnow()
            existing.expires_at = datetime.utcnow() + timedelta(days=1)
            return existing
        else:
            new_state = ConversationState(
                user_id=user_id,
                active_intent=intent,
                pending_payload=payload,
                updated_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=1),
            )
            session.add(new_state)
            await session.flush()
            return new_state

    async def clear(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        existing = await self.get_active(session, user_id)
        if existing is not None:
            await session.delete(existing)
            await session.flush()

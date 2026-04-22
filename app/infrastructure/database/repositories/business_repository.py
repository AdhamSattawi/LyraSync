import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.models.business_profile import BusinessProfile


class BusinessRepository:
    async def get_currency_code(
        self, business_id: uuid.UUID, session: AsyncSession
    ) -> str:
        stmt = select(BusinessProfile.currency_code).where(
            BusinessProfile.id == business_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(
        self, business_id: uuid.UUID, session: AsyncSession
    ) -> BusinessProfile | None:
        stmt = select(BusinessProfile).where(BusinessProfile.id == business_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

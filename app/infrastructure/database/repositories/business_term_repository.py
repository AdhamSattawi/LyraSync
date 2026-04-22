from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from app.domain.models.job_item import JobItem
from app.domain.models.job import Job
from app.domain.models.business_profile import BusinessProfile


class BusinessTermRepository:

    async def get_top_terms(self, session: AsyncSession, profession: str) -> list[str]:
        stmt = (
            select(distinct(JobItem.description))
            .join(Job)
            .join(BusinessProfile)
            .where(BusinessProfile.profession == profession)
            .limit(100)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

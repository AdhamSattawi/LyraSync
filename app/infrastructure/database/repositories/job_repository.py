from app.domain.models.job import Job
from app.domain.models.client import Client
from app.domain.models.job_item import JobItem
from app.domain.enums.job_status import JobStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.infrastructure.database.repositories.base_repository import BaseRepository
import uuid


class JobRepository(BaseRepository[Job]):
    def __init__(self):
        super().__init__(Job)

    async def find_by_title(
        self, business_id: uuid.UUID, title: str, session: AsyncSession
    ) -> Job | None:
        stmt = (
            select(Job)
            .options(selectinload(Job.items))
            .where(
                Job.business_id == business_id,
                Job.title.ilike(title),
                Job.is_deleted == False,
            )
        )
        return (await session.execute(stmt)).scalars().first()

    async def find_quotes_for_client(
        self, business_id: uuid.UUID, client_name: str, session: AsyncSession
    ) -> list[Job]:
        stmt = (
            select(Job)
            .options(selectinload(Job.items))
            .join(Client)
            .where(
                Client.business_id == business_id,
                Client.name.ilike(client_name),
                Job.status == JobStatus.QUOTE,
                Job.is_deleted == False,
            )
        )
        return (await session.execute(stmt)).scalars().all()

    async def get_total_price(self, job_id: uuid.UUID, session: AsyncSession) -> float:
        stmt = select(func.sum(JobItem.total_price)).where(JobItem.job_id == job_id)
        return (await session.execute(stmt)).scalar() or 0.0

    async def find_by_business_id(
        self, business_id: uuid.UUID, session: AsyncSession
    ) -> list[Job]:
        stmt = (
            select(Job)
            .options(selectinload(Job.items))
            .where(Job.business_id == business_id, Job.is_deleted == False)
        )
        return (await session.execute(stmt)).scalars().all()

    async def get_next_invoice_number(
        self, business_id: uuid.UUID, status: JobStatus, session: AsyncSession
    ) -> str:
        """
        Generates the next sequential invoice or quote number for a business.
        e.g., INV-0001 or QUOTE-0001
        """
        prefix = "INV" if status == JobStatus.INVOICE else "QUOTE"
        
        # Pattern to match: PREFIX-XXXX (where XXXX is any number of digits)
        pattern = f"{prefix}-%"
        
        stmt = (
            select(func.max(Job.invoice_number))
            .where(
                Job.business_id == business_id,
                Job.invoice_number.like(pattern)
            )
        )
        max_num_str = (await session.execute(stmt)).scalar()
        
        if not max_num_str:
            return f"{prefix}-0001"
        
        try:
            # Extract number part and increment
            current_num = int(max_num_str.split("-")[1])
            next_num = current_num + 1
            return f"{prefix}-{str(next_num).zfill(4)}"
        except (IndexError, ValueError):
            # Fallback if parsing fails
            return f"{prefix}-0001"

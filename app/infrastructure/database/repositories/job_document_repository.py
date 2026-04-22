from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.domain.models.job_document import JobDocument
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.domain.enums.job_document_status import JobDocumentStatus


class JobDocumentRepository(BaseRepository[JobDocument]):
    def __init__(self):
        super().__init__(JobDocument)

    async def track_job_document(
        self,
        job_id: uuid.UUID,
        document_template_id: uuid.UUID,
        document_url: str,
        created_by_id: uuid.UUID,
        session: AsyncSession,
    ) -> JobDocument:
        job_document = JobDocument(
            job_id=job_id,
            document_template_id=document_template_id,
            document_url=document_url,
            created_by_id=created_by_id,
            status=JobDocumentStatus.GENERATED,
        )
        return await self.save(job_document, session)

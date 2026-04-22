from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.domain.models.document_template import DocumentTemplate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class DocumentTemplateRepository(BaseRepository[DocumentTemplate]):
    def __init__(self):
        super().__init__(DocumentTemplate)

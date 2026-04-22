from abc import ABC, abstractmethod
import uuid
from sqlalchemy.ext.asyncio import AsyncSession


class DocumentContextBuilder(ABC):
    @abstractmethod
    async def build_context(self, entity_id: uuid.UUID, session: AsyncSession) -> dict:
        """
        Fetches necessary data for a specific entity type (e.g. Job)
        and transforms it into a standard Jinja2 context for PDF rendering.
        """
        raise NotImplementedError

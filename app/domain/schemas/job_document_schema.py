from app.domain.schemas.base_schema import BaseSchema
from pydantic import ConfigDict
from datetime import datetime
import uuid
from typing import Optional
from app.domain.enums.job_document_status import JobDocumentStatus


class JobDocumentBase(BaseSchema):
    document_url: Optional[str] = None
    status: JobDocumentStatus


class JobDocumentCreate(JobDocumentBase):
    model_config = ConfigDict(extra="ignore")


class JobDocumentUpdate(JobDocumentBase):
    model_config = ConfigDict(extra="ignore")


class JobDocument(JobDocumentBase):
    id: uuid.UUID
    job_id: uuid.UUID
    document_template_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by_id: uuid.UUID

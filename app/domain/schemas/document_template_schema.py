from app.domain.schemas.base_schema import BaseSchema
from pydantic import ConfigDict
from datetime import datetime
import uuid
from typing import Optional


class DocumentTemplateBase(BaseSchema):
    name: str
    description: Optional[str] = None
    system_prompt_override: Optional[str] = None
    type: str
    content: str
    html: str


class DocumentTemplateCreate(DocumentTemplateBase):
    model_config = ConfigDict(extra="ignore")


class DocumentTemplateUpdate(DocumentTemplateBase):
    model_config = ConfigDict(extra="ignore")


class DocumentTemplate(DocumentTemplateBase):
    id: uuid.UUID
    business_id: uuid.UUID
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_by_id: uuid.UUID
    updated_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

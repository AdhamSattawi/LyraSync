from datetime import datetime
import uuid
from typing import Optional, Any
from app.domain.schemas.base_schema import BaseSchema
from pydantic import ConfigDict
from app.domain.enums.job_status import JobStatus
from app.domain.schemas.job_item_schema import LineItemSchema


# ── LLM Extraction Schema ─────────────────────────────────────────
class JobExtract(BaseSchema):
    model_config = ConfigDict(extra="ignore")
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    client_name: str
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    items: list[LineItemSchema]


# ── Internal Service Schema ───────────────────────────────────────
class JobCreate(BaseSchema):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    status: JobStatus
    raw_data: str
    parsed_data: dict[str, Any]
    client_name: str
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    client_id: Optional[uuid.UUID] = None
    items: list[LineItemSchema]


class JobIdentifier(BaseSchema):
    model_config = ConfigDict(extra="ignore")
    job_title: str
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_email: Optional[str] = None


class JobUpdate(BaseSchema):
    model_config = ConfigDict(extra="ignore")
    target_job: JobIdentifier
    items: Optional[list[LineItemSchema]] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    status: Optional[JobStatus] = None


# ── Response Schema ───────────────────────────────────────────────
class JobSchema(BaseSchema):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    status: JobStatus
    raw_data: str
    parsed_data: dict[str, Any]
    business_id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    total_price: Optional[int] = None
    created_by_id: uuid.UUID
    invoice_number: Optional[str] = None
    currency_code: str
    items: list = []

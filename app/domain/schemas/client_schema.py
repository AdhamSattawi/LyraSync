from datetime import datetime
import uuid
from typing import Optional
from app.domain.schemas.base_schema import BaseSchema
from pydantic import ConfigDict


class ClientBase(BaseSchema):
    name: str
    email: Optional[str] = None
    phone: str
    phone_country_code: str
    address: str
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    model_config = ConfigDict(extra="ignore")


class ClientUpdate(ClientBase):
    model_config = ConfigDict(extra="ignore")


class Client(ClientBase):
    id: uuid.UUID
    business_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool

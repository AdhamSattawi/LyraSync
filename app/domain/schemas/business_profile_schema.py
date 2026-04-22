from datetime import datetime
import uuid
from typing import Optional
from app.domain.schemas.base_schema import BaseSchema
from pydantic import ConfigDict
from app.domain.enums.professions import Profession


class BusinessProfileBase(BaseSchema):
    name: str
    email: Optional[str] = None
    phone: str
    phone_country_code: str
    address: str
    profession: Profession
    logo: Optional[bytes] = None
    description: Optional[str] = None
    country: str
    city: Optional[str] = None
    country_code: Optional[str] = None
    tax_id: Optional[str] = None
    tax_rate_percent: float = 0.0
    timezone: str
    currency_code: str


class BusinessProfileCreate(BusinessProfileBase):
    model_config = ConfigDict(extra="ignore")


class BusinessProfileUpdate(BusinessProfileBase):
    model_config = ConfigDict(extra="ignore")


class BusinessProfile(BusinessProfileBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool

from datetime import datetime
import uuid
from typing import Optional
from app.domain.schemas.base_schema import BaseSchema
from pydantic import ConfigDict
from app.domain.enums.user_role import UserRole


class UserBase(BaseSchema):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    phone_country_code: str
    language_preference: str = "en"
    role: UserRole


class UserCreate(UserBase):
    model_config = ConfigDict(extra="ignore")


class UserUpdate(UserBase):
    model_config = ConfigDict(extra="ignore")


class User(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    business_id: uuid.UUID
    is_active: bool


class TokenPayload(BaseSchema):
    sub: Optional[str] = None

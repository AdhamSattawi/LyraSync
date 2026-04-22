import uuid
from typing import Optional
from pydantic import ConfigDict, field_validator
from app.domain.schemas.base_schema import BaseSchema
from app.domain.enums.professions import Profession


class BusinessSetupRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    # Business
    business_name: str
    business_phone: str
    business_address: str
    profession: Profession
    country: str

    # Optional overrides — derived from country if not provided
    timezone: Optional[str] = None
    currency_code: Optional[str] = None

    # Owner (the first OWNER user)
    owner_first_name: str
    owner_last_name: str
    owner_phone: str
    owner_email: Optional[str] = None
    owner_password: str

    @field_validator("profession", mode="before")
    @classmethod
    def lowercase_profession(cls, v):
        return v.lower() if isinstance(v, str) else v


class BusinessSetupResponse(BaseSchema):
    business_id: uuid.UUID
    user_id: uuid.UUID
    business_name: str
    message: str  # "Business registered successfully."

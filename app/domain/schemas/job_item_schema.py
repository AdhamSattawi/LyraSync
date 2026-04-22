from app.domain.schemas.base_schema import BaseSchema
from typing import Optional
import uuid
from datetime import datetime

from pydantic import Field


class LineItemSchema(BaseSchema):
    description: str
    quantity: float
    unit_price: int = Field(
        description="The unit price in the smallest currency denomination (e.g., cents, pence, agorot). Convert floats to this integer format."
    )
    total_price: int = Field(
        description="The total price in the smallest currency denomination (unit_price * quantity)."
    )


class LineItemCreate(BaseSchema):
    pass


class LineItemUpdate(BaseSchema):
    pass


class ItemSchema(LineItemSchema):
    id: uuid.UUID
    job_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

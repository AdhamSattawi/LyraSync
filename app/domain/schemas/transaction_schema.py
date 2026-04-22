from pydantic import BaseModel, Field, ConfigDict
import uuid
from datetime import datetime
from app.domain.enums.transaction_type import TransactionType


class TransactionExtract(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: TransactionType = Field(
        ..., description="Whether this is an 'income' or 'expense'"
    )
    amount: int = Field(
        ...,
        description="The total amount of the transaction in the smallest currency unit (e.g. cents/pence/agorot). Example: 50.00 becomes 5000.",
    )
    category: str = Field(
        ...,
        description="A short categorization. (e.g. 'materials', 'marketing', 'gas', 'service')",
    )
    description: str | None = Field(
        None, description="Detailed text specifying what this transaction was for"
    )
    status: str = Field(
        "cleared", description="Unless specified as pending, default to 'cleared'"
    )


class TransactionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID | None
    type: TransactionType
    amount: int
    currency_code: str
    category: str | None
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

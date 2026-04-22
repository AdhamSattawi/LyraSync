from pydantic import Field, ConfigDict
from app.domain.schemas.base_schema import BaseSchema
from typing import Optional

class PayPlusWebhookPayload(BaseSchema):
    """
    Schema for PayPlus Webhook notifications.
    Based on typical PayPlus 'Transaction Approved' notification.
    """
    model_config = ConfigDict(extra='ignore')

    transaction_type: str = Field(alias="transaction_type")
    status: str = Field(alias="status")
    amount: float = Field(alias="amount")
    currency: str = Field(alias="currency")
    customer_uid: str = Field(alias="customer_uid")
    external_id: Optional[str] = Field(None, alias="external_id") # This would be our business_id or a unique sub id
    transaction_uid: str = Field(alias="transaction_uid")
    approval_number: str = Field(alias="approval_number")

from sqlalchemy import String, TIMESTAMP, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime
from app.infrastructure.database.database import Base

class ProcessedWebhook(Base):
    __tablename__ = "processed_webhooks"

    # Suppress inherited fields from Base that we don't need for this log table
    id = None
    created_at = None
    updated_at = None

    # Twilio sends MessageSid or SmsSid
    # PayPlus sends transaction_uid
    webhook_id: Mapped[str] = mapped_column(String, primary_key=True, index=True, unique=True)
    provider: Mapped[str] = mapped_column(String, nullable=False) # 'twilio', 'payplus'
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

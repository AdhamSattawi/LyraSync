from app.infrastructure.database.database import Base
from sqlalchemy import String, TIMESTAMP, ForeignKey, LargeBinary, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.domain.enums.professions import Profession
from sqlalchemy import Enum
from typing import TYPE_CHECKING, Optional
from datetime import datetime

if TYPE_CHECKING:
    from app.domain.models.user import User
    from app.domain.models.job import Job
    from app.domain.models.client import Client
    from app.domain.models.document_template import DocumentTemplate
    from app.domain.models.transaction import Transaction
    from app.domain.models.message import Message


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone_country_code: Mapped[str] = mapped_column(
        String, nullable=False, default="+972"
    )
    address: Mapped[str] = mapped_column(String, nullable=False)
    profession: Mapped[Profession] = mapped_column(Enum(Profession), nullable=False)
    logo: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=False)
    country_code: Mapped[str] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    tax_id: Mapped[str] = mapped_column(String, nullable=True)
    tax_rate_percent: Mapped[float] = mapped_column(Float, default=0.0)
    timezone: Mapped[str] = mapped_column(String, nullable=False)
    currency_code: Mapped[str] = mapped_column(String, nullable=False)
    language_code: Mapped[str] = mapped_column(String, nullable=False, default="en")
    date_format: Mapped[str] = mapped_column(String, nullable=False, default="%d/%m/%Y")
    text_direction: Mapped[str] = mapped_column(String, nullable=False, default="ltr")
    default_invoice_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "document_templates.id",
            use_alter=True,
            name="fk_business_profiles_default_invoice_template_id",
        ),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Subscription Management
    subscription_plan: Mapped[str] = mapped_column(String, default="trial", nullable=False)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    payplus_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    user: Mapped[list["User"]] = relationship("User", back_populates="business")
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="business")
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="business")
    document_templates: Mapped[list["DocumentTemplate"]] = relationship(
        "DocumentTemplate", 
        back_populates="business",
        foreign_keys="[DocumentTemplate.business_id]"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="business"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="business"
    )

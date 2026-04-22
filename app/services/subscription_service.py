import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.models.business_profile import BusinessProfile
from app.domain.schemas.payplus_schema import PayPlusWebhookPayload
from app.domain.exceptions.exceptions import DomainException

class SubscriptionService:
    def __init__(self, session_maker: AsyncSession):
        self.session_maker = session_maker

    async def process_payplus_webhook(self, payload: PayPlusWebhookPayload):
        """
        Handles payment confirmation from PayPlus.
        Activates or extends business subscription.
        """
        if payload.status != "success":
            return {"message": "Ignored unsuccessful transaction"}

        async with self.session_maker() as session:
            # 1. Resolve business
            # external_id should contain our business_id UUID
            try:
                business_id = uuid.UUID(payload.external_id)
            except (ValueError, TypeError):
                raise DomainException(f"Invalid external_id: {payload.external_id}")

            business = await session.get(BusinessProfile, business_id)
            if not business:
                raise DomainException(f"Business {business_id} not found")

            # 2. Update subscription
            # For MVP: Any successful payment grants 1 month of 'PRO' plan
            business.subscription_plan = "pro"
            business.payplus_customer_id = payload.customer_uid
            
            # Extend expiration
            current_expiry = business.subscription_expires_at or datetime.now()
            if current_expiry < datetime.now():
                current_expiry = datetime.now()
            
            business.subscription_expires_at = current_expiry + timedelta(days=30)
            business.is_active = True

            await session.commit()
            return {"message": f"Subscription activated for {business.name}", "expires_at": business.subscription_expires_at}

from fastapi import APIRouter, Depends, Request, Response
from app.domain.schemas.payplus_schema import PayPlusWebhookPayload
from app.services.subscription_service import SubscriptionService
from app.api.dependencies import get_subscription_service, get_db, logger
from app.infrastructure.database.repositories.webhook_repository import WebhookRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/payplus/webhook")
async def payplus_webhook(
    payload: PayPlusWebhookPayload,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for PayPlus payment notifications.
    """
    logger.info(f"Received PayPlus webhook: {payload.transaction_uid} for customer {payload.customer_uid}")
    
    # ── Idempotency Check [INFRA-01] ────────────────────────────────────
    webhook_repo = WebhookRepository()
    if await webhook_repo.is_processed(payload.transaction_uid, db):
        logger.info(f"Ignoring duplicate PayPlus webhook: {payload.transaction_uid}")
        return {"message": "Already processed"}

    result = await subscription_service.process_payplus_webhook(payload)
    
    # Mark as processed after success
    await webhook_repo.mark_as_processed(
        webhook_id=payload.transaction_uid,
        provider="payplus",
        payload=payload.model_dump(mode='json'),
        session=db
    )
    await db.commit()
    
    return result

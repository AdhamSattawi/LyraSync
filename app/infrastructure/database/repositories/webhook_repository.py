from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.models.processed_webhook import ProcessedWebhook

class WebhookRepository:
    async def is_processed(self, webhook_id: str, session: AsyncSession) -> bool:
        stmt = select(ProcessedWebhook).where(ProcessedWebhook.webhook_id == webhook_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def mark_as_processed(self, webhook_id: str, provider: str, payload: dict, session: AsyncSession):
        processed = ProcessedWebhook(
            webhook_id=webhook_id,
            provider=provider,
            payload=payload
        )
        session.add(processed)
        await session.flush()

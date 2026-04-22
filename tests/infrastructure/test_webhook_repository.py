import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.database.repositories.webhook_repository import WebhookRepository
from app.domain.models.processed_webhook import ProcessedWebhook

@pytest.mark.asyncio
async def test_webhook_idempotency_logic():
    session = AsyncMock()
    repo = WebhookRepository()
    webhook_id = "test-sid-123"
    
    # 1. First check - not processed
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result
    
    is_proc = await repo.is_processed(webhook_id, session)
    assert is_proc is False
    
    # 2. Mark as processed
    await repo.mark_as_processed(webhook_id, "twilio", {"data": "test"}, session)
    assert session.add.called
    
    # 3. Second check - now processed
    mock_result_2 = MagicMock()
    mock_result_2.scalar_one_or_none.return_value = MagicMock(spec=ProcessedWebhook)
    session.execute.return_value = mock_result_2
    
    is_proc = await repo.is_processed(webhook_id, session)
    assert is_proc is True

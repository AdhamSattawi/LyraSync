import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from app.services.handlers.draft_quote_handler import DraftQuoteHandler
from app.services.handlers.update_job_handler import UpdateJobHandler
from app.services.handlers.delete_job_handler import DeleteJobHandler
from app.services.handlers.convert_invoice_handler import ConvertInvoiceHandler
from app.domain.schemas.job_schema import JobExtract, JobUpdate, JobIdentifier, JobSchema
from app.domain.schemas.handler_reply import HandlerReply

@pytest.fixture
def job_service():
    return AsyncMock()

@pytest.mark.asyncio
async def test_draft_quote_handler(job_service):
    handler = DraftQuoteHandler(job_service)
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    extracted_data = MagicMock(spec=JobExtract)
    
    mock_job = MagicMock(spec=JobSchema)
    mock_job.title = "Test Job"
    mock_job.invoice_number = "Q-001"
    mock_job.total_price = 50000 # 500.00
    mock_job.currency_code = "ILS"
    job_service.draft_quote.return_value = mock_job
    
    result = await handler.execute(business_id, user_id, extracted_data)
    
    assert "Q-001" in result
    assert "500.00 ILS" in result
    job_service.draft_quote.assert_awaited_once_with(business_id, user_id, extracted_data)

@pytest.mark.asyncio
async def test_update_job_handler(job_service):
    handler = UpdateJobHandler(job_service)
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    extracted_data = MagicMock(spec=JobUpdate)
    
    mock_job = MagicMock(spec=JobSchema)
    mock_job.title = "Updated Job"
    job_service.update_job.return_value = mock_job
    
    result = await handler.execute(business_id, user_id, extracted_data)
    
    assert "Updated job 'Updated Job' successfully" in result
    job_service.update_job.assert_awaited_once_with(business_id, user_id, extracted_data)

@pytest.mark.asyncio
async def test_delete_job_handler(job_service):
    handler = DeleteJobHandler(job_service)
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    extracted_data = MagicMock(spec=JobIdentifier)
    
    job_service.delete_job.return_value = "Job deleted."
    
    result = await handler.execute(business_id, user_id, extracted_data)
    
    assert result == "Job deleted."
    job_service.delete_job.assert_awaited_once_with(business_id, user_id, extracted_data)

@pytest.mark.asyncio
async def test_convert_invoice_handler(job_service):
    handler = ConvertInvoiceHandler(job_service)
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    extracted_data = MagicMock(spec=JobIdentifier)
    
    mock_reply = HandlerReply(text="Invoice ready", media_url="http://pdf.com")
    job_service.convert_to_invoice.return_value = mock_reply
    
    result = await handler.execute(business_id, user_id, extracted_data)
    
    assert result == mock_reply
    job_service.convert_to_invoice.assert_awaited_once_with(business_id, user_id, extracted_data)

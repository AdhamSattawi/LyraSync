import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.job_service import JobService
from app.domain.schemas.job_schema import JobExtract, JobIdentifier, JobUpdate
from app.domain.schemas.job_item_schema import LineItemSchema
from app.domain.enums.job_status import JobStatus
from app.domain.models.job import Job
from app.domain.models.client import Client
from app.domain.models.user import User
from app.domain.models.business_profile import BusinessProfile
from app.domain.models.job_item import JobItem
from app.domain.models.transaction import Transaction
from app.domain.models.message import Message
from app.domain.models.document_template import DocumentTemplate
from app.domain.models.job_document import JobDocument
from app.domain.models.conversation_state import ConversationState

@pytest.fixture
def session_maker():
    session_mock = MagicMock(spec=AsyncSession)
    session_mock.commit = AsyncMock()
    session_mock.flush = AsyncMock()
    session_mock.refresh = AsyncMock()
    session_mock.add = MagicMock()
    session_mock.execute = AsyncMock()
    
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session_mock
    return MagicMock(return_value=session_context)

@pytest.fixture
def client_repo():
    return AsyncMock()

@pytest.fixture
def job_repo():
    return AsyncMock()

@pytest.fixture
def business_repo():
    return AsyncMock()

@pytest.fixture
def document_service():
    return AsyncMock()

@pytest.fixture
def job_service(session_maker, client_repo, job_repo, business_repo, document_service):
    return JobService(
        session_maker=session_maker,
        client_repository=client_repo,
        job_repository=job_repo,
        business_repository=business_repo,
        document_service=document_service
    )

@pytest.mark.asyncio
async def test_draft_quote_creates_new_job(job_service, client_repo, job_repo, business_repo):
    # 1. Setup
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    job_data = JobExtract(
        title="Fix Pipe",
        client_name="Alice",
        items=[LineItemSchema(description="Labor", quantity=1.0, unit_price=10000, total_price=10000)]
    )
    
    client_repo.find_by_name.return_value = None # New client
    # Mock save to simulate DB side-effects
    async def mock_save_client(client, session):
        client.id = uuid.uuid4()
    client_repo.save.side_effect = mock_save_client

    async def mock_save_job(job, session):
        job.id = uuid.uuid4()
        job.created_at = datetime.now()
        job.updated_at = datetime.now()
    job_repo.save.side_effect = mock_save_job

    job_repo.get_next_invoice_number.return_value = "QUOTE-0001"
    business_repo.get_currency_code.return_value = "GBP"

    # 2. Execute
    result = await job_service.draft_quote(business_id, user_id, job_data)

    # 3. Assertions
    assert result.title == "Fix Pipe"
    assert result.invoice_number == "QUOTE-0001"
    assert result.total_price == 10000
    
    # Verify repository calls
    assert client_repo.save.called
    assert job_repo.save.called
    job_repo.get_next_invoice_number.assert_awaited_with(business_id, JobStatus.QUOTE, ANY)

@pytest.mark.asyncio
async def test_convert_to_invoice_success(job_service, job_repo, business_repo, document_service):
    # 1. Setup
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    identifier = JobIdentifier(client_name="Alice", job_title="Fix Pipe")
    
    target_job = MagicMock(spec=Job)
    target_job.id = uuid.uuid4()
    target_job.title = "Fix Pipe"
    target_job.currency_code = "GBP"
    target_job.total_price = 10000
    
    job_repo.find_quotes_for_client.return_value = [target_job]
    job_repo.get_total_price.return_value = 10000
    
    business = MagicMock()
    business.default_invoice_template_id = uuid.uuid4()
    business_repo.find_by_id.return_value = business
    
    document_service.generate_document.return_value = "https://azure.com/invoice.pdf"

    # 2. Execute
    result = await job_service.convert_to_invoice(business_id, user_id, identifier)

    # 3. Assertions
    assert target_job.status == JobStatus.INVOICE
    assert target_job.is_finalized is True
    assert "Invoice ready" in result.text
    assert result.media_url == "https://azure.com/invoice.pdf"
    
    document_service.generate_document.assert_awaited_once()

@pytest.mark.asyncio
async def test_convert_to_invoice_ambiguous(job_service, job_repo):
    # 1. Setup
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    identifier = JobIdentifier(client_name="Alice", job_title="Fix Pipe")
    
    # Multiple quotes found
    job_repo.find_quotes_for_client.return_value = [MagicMock(), MagicMock()]

    # 2. Execute
    result = await job_service.convert_to_invoice(business_id, user_id, identifier)

    # 3. Assertions
    assert "found multiple open quotes" in result
    assert isinstance(result, str)

@pytest.mark.asyncio
async def test_update_job_finalized_fails(job_service, job_repo):
    # 1. Setup
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    update_data = JobUpdate(
        target_job=JobIdentifier(job_title="Old Job"),
        title="New Title"
    )
    
    finalized_job = MagicMock(spec=Job)
    finalized_job.is_finalized = True
    job_repo.find_by_title.return_value = finalized_job

    # 2. Execute
    result = await job_service.update_job(business_id, user_id, update_data)

    # 3. Assertions
    assert "is finalized and cannot be updated" in result

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.document_service import DocumentService
from app.domain.models.document_template import DocumentTemplate
from app.domain.models.user import User
from app.domain.models.business_profile import BusinessProfile
from app.domain.models.job import Job
from app.domain.models.job_item import JobItem
from app.domain.models.transaction import Transaction
from app.domain.models.message import Message
from app.domain.models.job_document import JobDocument
from app.domain.models.client import Client
from app.domain.models.conversation_state import ConversationState

@pytest.fixture
def session():
    session_mock = MagicMock(spec=AsyncSession)
    session_mock.get = AsyncMock()
    return session_mock

@pytest.fixture
def job_doc_repo():
    return AsyncMock()

@pytest.fixture
def storage_service():
    return AsyncMock()

@pytest.fixture
def document_service(session, job_doc_repo, storage_service):
    # Patch the internal components during initialization
    with patch("app.services.document_service.WeasyPrintGenerator"), \
         patch("app.services.document_service.InvoiceContextBuilder"), \
         patch("app.services.document_service.QuoteContextBuilder"):
        
        service = DocumentService(
            session=session,
            job_doc_repo=job_doc_repo,
            storage_service=storage_service
        )
        return service

@pytest.mark.asyncio
async def test_generate_document_success(document_service, session, storage_service, job_doc_repo):
    # 1. Setup
    job_id = uuid.uuid4()
    template_id = uuid.uuid4()
    user_id = uuid.uuid4()
    business_id = uuid.uuid4()
    
    template = MagicMock(spec=DocumentTemplate)
    template.id = template_id
    template.type = "INVOICE"
    template.html = "<html>{{ title }}</html>"
    template.business_id = business_id
    session.get.return_value = template
    
    # Mock the builder registered in __init__
    mock_builder = AsyncMock()
    mock_builder.build_context.return_value = {"title": "Test Invoice"}
    document_service._builders["INVOICE"] = mock_builder
    
    # Mock PDF generator
    document_service.pdf_generator.generate = AsyncMock(return_value=b"pdf-content")
    
    storage_service.upload.return_value = "https://azure.com/test.pdf"

    # 2. Execute
    url = await document_service.generate_document(job_id, template_id, user_id)

    # 3. Assertions
    assert url == "https://azure.com/test.pdf"
    mock_builder.build_context.assert_awaited_once_with(job_id, session)
    storage_service.upload.assert_awaited_once()
    job_doc_repo.track_job_document.assert_awaited_once()

@pytest.mark.asyncio
async def test_generate_document_invalid_template(document_service, session):
    # 1. Setup
    session.get.return_value = None # Template not found
    
    # 2. Execute & Assert
    with pytest.raises(ValueError) as exc:
        await document_service.generate_document(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    
    assert "not found" in str(exc.value)

@pytest.mark.asyncio
async def test_generate_document_unsupported_type(document_service, session):
    # 1. Setup
    template = MagicMock(spec=DocumentTemplate)
    template.type = "UNKNOWN"
    session.get.return_value = template
    
    # 2. Execute & Assert
    with pytest.raises(ValueError) as exc:
        await document_service.generate_document(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    
    assert "No ContextBuilder registered" in str(exc.value)

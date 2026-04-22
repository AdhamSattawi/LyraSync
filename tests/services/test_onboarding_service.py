import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.onboarding_service import OnboardingService
from app.domain.schemas.onboarding_schema import BusinessSetupRequest
from app.domain.enums.professions import Profession
from app.domain.models.business_profile import BusinessProfile
from app.domain.models.user import User
from app.domain.models.client import Client
from app.domain.models.document_template import DocumentTemplate
from app.domain.models.job import Job
from app.domain.models.job_item import JobItem
from app.domain.models.transaction import Transaction
from app.domain.models.message import Message
from app.domain.models.job_document import JobDocument
from app.domain.models.conversation_state import ConversationState
from app.domain.exceptions.exceptions import DomainException

@pytest.fixture
def session_maker():
    session_mock = MagicMock(spec=AsyncSession)
    session_mock.execute = AsyncMock()
    session_mock.commit = AsyncMock()
    session_mock.flush = AsyncMock()
    session_mock.rollback = AsyncMock()
    
    # Side effect to assign IDs to models when added to session
    def mock_add(obj):
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = uuid.uuid4()
    session_mock.add = MagicMock(side_effect=mock_add)
    
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session_mock
    return MagicMock(return_value=session_context)

@pytest.fixture
def onboarding_service(session_maker):
    return OnboardingService(session_maker=session_maker)

@pytest.mark.asyncio
async def test_register_business_success(onboarding_service, session_maker):
    # 1. Setup
    session = session_maker.return_value.__aenter__.return_value
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None # No existing user
    session.execute.return_value = mock_result
    
    request_data = BusinessSetupRequest(
        business_name="PlumbIt",
        business_phone="+447700900000",
        business_address="123 UK St",
        profession=Profession.PLUMBER,
        country="United Kingdom",
        owner_first_name="John",
        owner_last_name="Doe",
        owner_email="john@example.com",
        owner_password="securepassword123",
        owner_phone="+447700900000"
    )

    # Mock aiofiles.open to return a dummy template
    with patch("app.services.onboarding_service.aiofiles.open") as mock_open:
        mock_file = AsyncMock()
        mock_file.read.return_value = "<html><body>Invoice</body></html>"
        mock_open.return_value.__aenter__.return_value = mock_file

        # 2. Execute
        result = await onboarding_service.register_business(request_data)

        # 3. Assertions
        assert result.business_name == "PlumbIt"
        assert result.message == "Business registered successfully. You can now message the bot on WhatsApp."
        assert isinstance(result.business_id, uuid.UUID)
        assert isinstance(result.user_id, uuid.UUID)
        assert session.commit.called
        assert session.add.call_count == 3 # Business, User, Template

@pytest.mark.asyncio
async def test_register_business_duplicate_phone_fails(onboarding_service, session_maker):
    # 1. Setup
    session = session_maker.return_value.__aenter__.return_value
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock(spec=User) # User exists
    session.execute.return_value = mock_result
    
    request_data = BusinessSetupRequest(
        business_name="PlumbIt",
        business_phone="+447700900000",
        business_address="123 UK St",
        profession=Profession.PLUMBER,
        country="United Kingdom",
        owner_first_name="John",
        owner_last_name="Doe",
        owner_email="john@example.com",
        owner_password="securepassword123",
        owner_phone="+447700900000"
    )

    # 2. Execute & Assert
    with pytest.raises(DomainException) as exc:
        await onboarding_service.register_business(request_data)
    
    assert "already registered" in str(exc.value)
    assert not session.commit.called

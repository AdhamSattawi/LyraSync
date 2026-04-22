import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.transaction_service import TransactionService
from app.domain.schemas.transaction_schema import TransactionExtract
from app.domain.enums.transaction_type import TransactionType
from app.domain.models.transaction import Transaction
from app.domain.models.user import User
from app.domain.models.business_profile import BusinessProfile
from app.domain.models.job import Job
from app.domain.models.job_item import JobItem
from app.domain.models.client import Client
from app.domain.models.message import Message
from app.domain.models.document_template import DocumentTemplate
from app.domain.models.job_document import JobDocument
from app.domain.models.conversation_state import ConversationState

@pytest.fixture
def session_maker():
    session_mock = MagicMock(spec=AsyncSession)
    session_mock.commit = AsyncMock()
    session_mock.refresh = AsyncMock()
    session_mock.execute = AsyncMock()
    session_mock.add = MagicMock()
    
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session_mock
    return MagicMock(return_value=session_context)

@pytest.fixture
def transaction_repo():
    return AsyncMock()

@pytest.fixture
def business_repo():
    return AsyncMock()

@pytest.fixture
def transaction_service(session_maker, transaction_repo, business_repo):
    return TransactionService(
        session_maker=session_maker,
        transaction_repository=transaction_repo,
        business_repository=business_repo
    )

@pytest.mark.asyncio
async def test_log_transaction_success(transaction_service, transaction_repo, business_repo):
    # 1. Setup
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    data = TransactionExtract(
        type=TransactionType.INCOME,
        amount=5000,
        category="Service",
        description="Fix faucet",
        status="completed"
    )
    
    business_repo.get_currency_code.return_value = "ILS"
    
    async def mock_save(transaction, session):
        transaction.id = uuid.uuid4()
        transaction.created_at = datetime.now()
        transaction.updated_at = datetime.now()
    transaction_repo.save.side_effect = mock_save

    # 2. Execute
    result = await transaction_service.log_transaction(business_id, user_id, data)

    # 3. Assertions
    assert result.amount == 5000
    assert result.currency_code == "ILS"
    assert transaction_repo.save.called

@pytest.mark.asyncio
async def test_get_cash_flow_summary(transaction_service, transaction_repo, business_repo):
    # 1. Setup
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    transaction_repo.get_balance.return_value = {
        "income": 100000, # 1000.00
        "expense": 20000, # 200.00
        "net": 80000      # 800.00
    }
    business_repo.get_currency_code.return_value = "USD"

    # 2. Execute
    result = await transaction_service.get_cash_flow(business_id, user_id)

    # 3. Assertions
    assert "Gross Income: 1,000.00 USD" in result
    assert "Total Expenses: 200.00 USD" in result
    assert "Net Cash Flow: 800.00 USD" in result

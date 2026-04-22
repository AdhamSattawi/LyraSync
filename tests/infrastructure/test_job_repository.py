import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.database.repositories.job_repository import JobRepository
from app.domain.enums.job_status import JobStatus

@pytest.mark.asyncio
async def test_get_next_invoice_number_first_record():
    """
    Ensures that if no records exist, it starts at 0001 with the correct prefix.
    """
    # 1. Setup
    repo = JobRepository()
    session = AsyncMock()
    business_id = uuid.uuid4()
    
    # Mock empty result from DB
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    session.execute.return_value = mock_result

    # 2. Execute
    next_num = await repo.get_next_invoice_number(business_id, JobStatus.QUOTE, session)

    # 3. Assert
    assert next_num == "QUOTE-0001"
    
    # Test for Invoice prefix
    mock_result.scalar.return_value = None
    next_inv = await repo.get_next_invoice_number(business_id, JobStatus.INVOICE, session)
    assert next_inv == "INV-0001"

@pytest.mark.asyncio
async def test_get_next_invoice_number_increments():
    """
    Ensures that it correctly increments the number part of the string.
    """
    # 1. Setup
    repo = JobRepository()
    session = AsyncMock()
    business_id = uuid.uuid4()
    
    # Mock finding 'QUOTE-0005'
    mock_result = MagicMock()
    mock_result.scalar.return_value = "QUOTE-0005"
    session.execute.return_value = mock_result

    # 2. Execute
    next_num = await repo.get_next_invoice_number(business_id, JobStatus.QUOTE, session)

    # 3. Assert
    assert next_num == "QUOTE-0006"

@pytest.mark.asyncio
async def test_get_next_invoice_number_handles_long_numbers():
    """
    Ensures it handles numbers > 9999 gracefully (it should just expand).
    """
    # 1. Setup
    repo = JobRepository()
    session = AsyncMock()
    business_id = uuid.uuid4()
    
    # Mock finding 'QUOTE-9999'
    mock_result = MagicMock()
    mock_result.scalar.return_value = "QUOTE-9999"
    session.execute.return_value = mock_result

    # 2. Execute
    next_num = await repo.get_next_invoice_number(business_id, JobStatus.QUOTE, session)

    # 3. Assert
    assert next_num == "QUOTE-10000"

@pytest.mark.asyncio
async def test_get_next_invoice_number_handles_malformed_string():
    """
    Ensures it returns 0001 if the prefix match logic fails.
    """
    # 1. Setup
    repo = JobRepository()
    session = AsyncMock()
    business_id = uuid.uuid4()
    
    # Mock finding a malformed string that doesn't follow the split('-') rule
    mock_result = MagicMock()
    mock_result.scalar.return_value = "MALFORMED"
    session.execute.return_value = mock_result

    # 2. Execute
    next_num = await repo.get_next_invoice_number(business_id, JobStatus.QUOTE, session)

    # 3. Assert
    assert next_num == "QUOTE-0001"

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from app.services.subscription_service import SubscriptionService
from app.domain.schemas.payplus_schema import PayPlusWebhookPayload
from app.domain.models.business_profile import BusinessProfile
from app.api.dependencies import get_db

@pytest.mark.asyncio
async def test_payplus_webhook_success():
    """
    Verifies that a successful PayPlus webhook updates the business subscription.
    """
    app = create_app()
    business_id = uuid.uuid4()
    
    # Mock DB session
    mock_db = AsyncMock()
    mock_db.execute.return_value = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None # Not processed
    app.dependency_overrides[get_db] = lambda: mock_db

    payload = {
        "transaction_type": "Charge",
        "status": "success",
        "amount": 100.0,
        "currency": "ILS",
        "customer_uid": "cust_123",
        "external_id": str(business_id),
        "transaction_uid": "tx_999",
        "approval_number": "123456"
    }
    
    with patch("app.api.routes.payplus.SubscriptionService.process_payplus_webhook") as mock_process:
        mock_process.return_value = {"message": "Success"}
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/webhooks/payplus/webhook", json=payload)
        
        assert response.status_code == 200
        mock_process.assert_called_once()
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_subscription_service_logic():
    """
    Unit test for the SubscriptionService.process_payplus_webhook logic.
    """
    business_id = uuid.uuid4()
    session_mock = AsyncMock()
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session_mock
    session_maker = MagicMock(return_value=session_context)
    
    service = SubscriptionService(session_maker=session_maker)
    
    payload = PayPlusWebhookPayload(
        transaction_type="Charge",
        status="success",
        amount=100.0,
        currency="ILS",
        customer_uid="cust_123",
        external_id=str(business_id),
        transaction_uid="tx_999",
        approval_number="123456"
    )
    
    mock_business = MagicMock(spec=BusinessProfile)
    mock_business.name = "Test Biz"
    mock_business.subscription_expires_at = None
    session_mock.get.return_value = mock_business
    
    result = await service.process_payplus_webhook(payload)
    
    assert "activated" in result["message"]
    assert mock_business.subscription_plan == "pro"
    assert mock_business.is_active is True
    assert mock_business.subscription_expires_at is not None
    assert session_mock.commit.called

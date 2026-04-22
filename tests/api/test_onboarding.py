import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from app.domain.schemas.onboarding_schema import BusinessSetupResponse
from app.domain.enums.professions import Profession

@pytest.mark.asyncio
async def test_register_business_endpoint():
    """
    Verifies that the /onboarding/register endpoint calls the service and returns 200.
    """
    app = create_app()
    
    request_payload = {
        "business_name": "Test Biz",
        "business_phone": "+1234567890",
        "business_address": "123 Test St",
        "profession": "plumber",
        "country": "United Kingdom",
        "owner_first_name": "Test",
        "owner_last_name": "User",
        "owner_email": "test@example.com",
        "owner_password": "password123",
        "owner_phone": "+1234567890"
    }
    
    mock_response = BusinessSetupResponse(
        business_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        business_name="Test Biz",
        message="Success"
    )
    
    with patch("app.api.routes.onboarding.OnboardingService.register_business") as mock_register:
        mock_register.return_value = mock_response
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/onboarding/register", json=request_payload)
        
        assert response.status_code == 200
        assert response.json()["business_name"] == "Test Biz"
        mock_register.assert_called_once()

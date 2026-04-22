import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app
from unittest.mock import patch, MagicMock, AsyncMock
from app.api.dependencies import get_agent_dispatcher, get_db
from app.services.agent_dispatcher import DispatcherResult

@pytest.mark.asyncio
async def test_webhook_rejects_missing_signature():
    """
    Ensures that the Twilio webhook route rejects requests without 
     the X-Twilio-Signature header.
    """
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/webhooks/twilio/whatsapp", data={"Body": "Hello"})
    
    # validate_twilio_request raises 403 Forbidden for missing/invalid signatures
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature():
    """
    Ensures that the Twilio webhook route rejects requests with 
    an invalid X-Twilio-Signature header.
    """
    app = create_app()
    headers = {"X-Twilio-Signature": "invalid-signature"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/webhooks/twilio/whatsapp", 
            data={"Body": "Hello"}, 
            headers=headers
        )
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_webhook_accepts_valid_signature_mocked():
    """
    Mocks the Twilio RequestValidator to verify that a 'valid' request 
    (one that passes validation) is allowed through the firewall.
    """
    app = create_app()
    
    # Override dependencies to avoid DB connection
    mock_dispatcher = AsyncMock()
    mock_dispatcher.process_message.return_value = DispatcherResult(reply="Mocked Reply")
    app.dependency_overrides[get_agent_dispatcher] = lambda: mock_dispatcher
    
    mock_db = AsyncMock()
    mock_db.execute.return_value = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None # Not processed
    app.dependency_overrides[get_db] = lambda: mock_db

    # We mock the validate method of the RequestValidator class
    with patch("app.api.dependencies.RequestValidator.validate") as mock_validate:
        mock_validate.return_value = True
        
        headers = {"X-Twilio-Signature": "fake-but-valid-looking"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # We don't care about the result of the dispatcher here, just that it didn't return 403
            response = await ac.post(
                "/api/v1/webhooks/twilio/whatsapp", 
                data={"Body": "Hello", "From": "whatsapp:+1234567890", "MessageSid": "SM123"}, 
                headers=headers
            )
        
        assert response.status_code == 200
    
    app.dependency_overrides.clear()

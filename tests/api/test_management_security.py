import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app
from app.core import security
from app.core.config import settings
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_management_api_rejects_missing_token():
    """
    Ensures that management routes are protected and reject requests 
    without an Authorization header.
    """
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Testing one of the management routes
        response = await ac.get("/api/v1/users/me")
    
    # OAuth2PasswordBearer returns 401 Unauthorized for missing token by default
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_management_api_rejects_invalid_token():
    """
    Ensures that management routes reject requests with an invalid/malformed token.
    """
    app = create_app()
    headers = {"Authorization": "Bearer invalid-token"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers=headers)
    
    # dependencies.get_current_user raises 403 for invalid tokens
    assert response.status_code == 403
    assert "Could not validate credentials" in response.json()["detail"]

@pytest.mark.asyncio
async def test_management_api_accepts_valid_token():
    """
    Verifies that a valid JWT token allows access to protected routes.
    """
    app = create_app()
    user_id = uuid.uuid4()
    business_id = uuid.uuid4()
    token = security.create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mock the database user retrieval inside get_current_user
    with patch("app.api.dependencies.AsyncSession.get") as mock_get:
        from app.domain.enums.user_role import UserRole
        from datetime import datetime
        
        mock_user = MagicMock() # Use MagicMock for attributes, not AsyncMock
        mock_user.id = user_id
        mock_user.business_id = business_id
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.email = "test@example.com"
        mock_user.phone = "+1234567890"
        mock_user.phone_country_code = "US"
        mock_user.language_preference = "en"
        mock_user.role = UserRole.OWNER
        mock_user.is_active = True
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        
        mock_get.return_value = mock_user
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == str(user_id)
        assert response.json()["email"] == "test@example.com"

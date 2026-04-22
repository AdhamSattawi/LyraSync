import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.profile_service import ProfileService
from app.domain.models.user import User
from app.domain.models.business_profile import BusinessProfile
from app.domain.schemas.user_schema import UserUpdate
from app.domain.schemas.business_profile_schema import BusinessProfileUpdate
from app.domain.enums.user_role import UserRole
from app.domain.enums.professions import Profession

@pytest.fixture
def session_maker():
    session_mock = MagicMock(spec=AsyncSession)
    session_mock.get = AsyncMock()
    session_mock.commit = AsyncMock()
    session_mock.refresh = AsyncMock()
    
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session_mock
    return MagicMock(return_value=session_context)

@pytest.fixture
def profile_service(session_maker):
    return ProfileService(session_maker=session_maker)

@pytest.mark.asyncio
async def test_update_user_me_success(profile_service, session_maker):
    # 1. Setup
    session = session_maker.return_value.__aenter__.return_value
    user_id = uuid.uuid4()
    
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    session.get.return_value = mock_user
    
    update_data = UserUpdate(
        first_name="New",
        last_name="Name",
        email="new@example.com",
        phone="+1234567890",
        phone_country_code="US",
        language_preference="he",
        role=UserRole.OWNER
    )

    # 2. Execute
    result = await profile_service.update_user_me(user_id, update_data)

    # 3. Assertions
    assert result.first_name == "New"
    assert result.language_preference == "he"
    assert session.commit.called

@pytest.mark.asyncio
async def test_update_business_me_success(profile_service, session_maker):
    # 1. Setup
    session = session_maker.return_value.__aenter__.return_value
    business_id = uuid.uuid4()
    
    mock_business = MagicMock(spec=BusinessProfile)
    mock_business.id = business_id
    session.get.return_value = mock_business
    
    update_data = BusinessProfileUpdate(
        name="Updated Biz",
        phone="+1234567890",
        phone_country_code="US",
        address="New Address",
        profession=Profession.PLUMBER,
        country="United Kingdom",
        timezone="Europe/London",
        currency_code="GBP"
    )

    # 2. Execute
    result = await profile_service.update_business_me(business_id, update_data)

    # 3. Assertions
    assert result.name == "Updated Biz"
    assert result.currency_code == "GBP"
    assert session.commit.called

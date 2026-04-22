import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.user import User
from app.domain.models.business_profile import BusinessProfile
from app.domain.schemas.user_schema import UserUpdate
from app.domain.schemas.business_profile_schema import BusinessProfileUpdate
from app.domain.exceptions.exceptions import DomainException

class ProfileService:
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def update_user_me(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        async with self.session_maker() as session:
            user = await session.get(User, user_id)
            if not user:
                raise DomainException("User not found")
            
            # Update fields
            user.first_name = data.first_name
            user.last_name = data.last_name
            user.email = data.email
            user.phone = data.phone
            user.phone_country_code = data.phone_country_code
            user.language_preference = data.language_preference
            # Role should probably not be updatable via /me for security
            
            await session.commit()
            await session.refresh(user)
            return user

    async def get_business_me(self, business_id: uuid.UUID) -> BusinessProfile:
        async with self.session_maker() as session:
            business = await session.get(BusinessProfile, business_id)
            if not business:
                raise DomainException("Business not found")
            return business

    async def update_business_me(self, business_id: uuid.UUID, data: BusinessProfileUpdate) -> BusinessProfile:
        async with self.session_maker() as session:
            business = await session.get(BusinessProfile, business_id)
            if not business:
                raise DomainException("Business not found")
            
            # Update fields
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(business, field, value)
            
            await session.commit()
            await session.refresh(business)
            return business

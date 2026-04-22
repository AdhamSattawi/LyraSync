from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.models.business_profile import BusinessProfile
from app.domain.models.user import User
from app.domain.enums.user_role import UserRole
from app.domain.schemas.onboarding_schema import (
    BusinessSetupRequest,
    BusinessSetupResponse,
)
from app.domain.exceptions.exceptions import DomainException
from app.core.security import hash_password
from app.core.country_defaults import get_country_defaults
from app.domain.models.document_template import DocumentTemplate
import aiofiles
import os


class OnboardingService:
    def __init__(self, session_maker: AsyncSession):
        self.session_maker = session_maker

    async def register_business(
        self, data: BusinessSetupRequest
    ) -> BusinessSetupResponse:
        async with self.session_maker() as session:
            try:
                # 1. Guard: phone must be unique
                existing = await session.execute(
                    select(User).where(User.phone == data.owner_phone)
                )
                if existing.scalar_one_or_none():
                    raise DomainException("This phone number is already registered.")

                # 2. Resolve country defaults
                defaults = get_country_defaults(data.country)

                # 3. Create BusinessProfile
                business = BusinessProfile(
                    name=data.business_name,
                    phone=data.business_phone,
                    phone_country_code=defaults["phone_country_code"],
                    address=data.business_address,
                    profession=data.profession,
                    country=data.country,
                    country_code=defaults["country_code"],
                    timezone=data.timezone or defaults["timezone"],
                    currency_code=data.currency_code or defaults["currency_code"],
                    language_code=defaults["language_code"],
                    date_format=defaults["date_format"],
                    text_direction=defaults["text_direction"],
                    is_active=True,
                )
                session.add(business)
                await session.flush()  # get business.id before creating User (FK dependency)

                # 4. Hash password immediately — never store plain text
                password_hash = hash_password(data.owner_password)

                # 5. Create OWNER User
                user = User(
                    first_name=data.owner_first_name,
                    last_name=data.owner_last_name,
                    phone=data.owner_phone,
                    phone_country_code=defaults["phone_country_code"],
                    email=data.owner_email,
                    role=UserRole.OWNER,
                    business_id=business.id,
                    password_hash=password_hash,
                    is_active=True,
                )
                session.add(user)

                # 6. Create default Invoice Template
                template_path = os.path.join(
                    "app", "infrastructure", "templates", "invoice.html"
                )
                async with aiofiles.open(
                    template_path, mode="r", encoding="utf-8"
                ) as f:
                    template_html = await f.read()

                default_template = DocumentTemplate(
                    name="Professional Invoice",
                    type="INVOICE",
                    content="Default professionally designed invoice template.",
                    html=template_html,
                    business_id=business.id,
                    created_by_id=user.id,
                    is_deleted=False,
                )
                session.add(default_template)
                await session.flush()

                # Link business to its default template
                business.default_invoice_template_id = default_template.id

                await session.commit()

                return BusinessSetupResponse(
                    business_id=business.id,
                    user_id=user.id,
                    business_name=business.name,
                    message="Business registered successfully. You can now message the bot on WhatsApp.",
                )

            except DomainException:
                raise  # Let the router handle these with a 400
            except Exception as e:
                await session.rollback()
                raise DomainException(f"Registration failed: {str(e)}")

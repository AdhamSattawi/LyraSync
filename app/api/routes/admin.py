from fastapi import APIRouter, Header, HTTPException, status
from app.domain.schemas.onboarding_schema import (
    BusinessSetupRequest,
    BusinessSetupResponse,
)
from app.services.onboarding_service import OnboardingService
from app.infrastructure.database.database import AsyncSessionLocal
from app.core.config import settings
from app.domain.exceptions.exceptions import DomainException

router = APIRouter()


def _check_admin_key(x_admin_key: str = Header(...)):
    """Dependency that validates the admin secret key from the X-Admin-Key header."""
    if x_admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key."
        )


@router.post("/setup", response_model=BusinessSetupResponse, status_code=201)
async def setup_business(
    payload: BusinessSetupRequest,
    x_admin_key: str = Header(..., alias="X-Admin-Key"),
):
    _check_admin_key(x_admin_key)
    service = OnboardingService(session_maker=AsyncSessionLocal)
    try:
        return await service.register_business(payload)
    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

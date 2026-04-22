from fastapi import APIRouter, Depends
from app.domain.schemas.onboarding_schema import (
    BusinessSetupRequest,
    BusinessSetupResponse,
)
from app.services.onboarding_service import OnboardingService
from app.api.dependencies import get_onboarding_service

router = APIRouter()


@router.post("/onboarding/register", response_model=BusinessSetupResponse)
async def register_business(
    data: BusinessSetupRequest,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> BusinessSetupResponse:
    """
    Unified registration endpoint for new businesses.
    Creates a BusinessProfile, an OWNER User, and default templates.
    """
    return await onboarding_service.register_business(data)

from typing import List, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import dependencies
from app.domain.models.user import User
from app.domain.schemas.client_schema import Client, ClientCreate
from app.domain.schemas.job_schema import JobSchema
from app.domain.schemas.user_schema import User as UserSchema, UserUpdate
from app.domain.schemas.business_profile_schema import BusinessProfile as BusinessProfileSchema, BusinessProfileUpdate
from app.infrastructure.database.repositories.client_repository import ClientRepository
from app.infrastructure.database.repositories.job_repository import JobRepository
from app.infrastructure.database.repositories.transaction_repository import TransactionRepository
from app.services.job_service import JobService
from app.services.transaction_service import TransactionService
from app.services.profile_service import ProfileService

router = APIRouter()


@router.get("/users/me", response_model=UserSchema)
async def get_user_me(
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get current user profile
    """
    return UserSchema.model_validate(current_user)


@router.put("/users/me", response_model=UserSchema)
async def update_user_me(
    data: UserUpdate,
    current_user: User = Depends(dependencies.get_current_user),
    profile_service: ProfileService = Depends(dependencies.get_profile_service),
) -> Any:
    """
    Update current user profile
    """
    return await profile_service.update_user_me(current_user.id, data)


@router.get("/business/me", response_model=BusinessProfileSchema)
async def get_business_me(
    current_user: User = Depends(dependencies.get_current_user),
    profile_service: ProfileService = Depends(dependencies.get_profile_service),
) -> Any:
    """
    Get current business profile
    """
    return await profile_service.get_business_me(current_user.business_id)


@router.put("/business/me", response_model=BusinessProfileSchema)
async def update_business_me(
    data: BusinessProfileUpdate,
    current_user: User = Depends(dependencies.get_current_user),
    profile_service: ProfileService = Depends(dependencies.get_profile_service),
) -> Any:
    """
    Update current business profile
    """
    return await profile_service.update_business_me(current_user.business_id, data)


@router.get("/clients", response_model=List[Client])
async def list_clients(
    db: AsyncSession = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    List all clients for the business
    """
    repo = ClientRepository()
    clients = await repo.find_all_by_business(current_user.business_id, db)
    return [Client.model_validate(c) for c in clients]


@router.get("/jobs", response_model=List[JobSchema])
async def list_jobs(
    current_user: User = Depends(dependencies.get_current_user),
    job_service: JobService = Depends(dependencies.get_job_service),
) -> Any:
    """
    List all jobs for the business
    """
    res = await job_service.list_jobs(current_user.business_id, current_user.id)
    if isinstance(res, str):
        return []
    return res


@router.get("/balance")
async def get_balance(
    current_user: User = Depends(dependencies.get_current_user),
    transaction_service: TransactionService = Depends(dependencies.get_transaction_service),
) -> Any:
    """
    Get P&L summary
    """
    res = await transaction_service.get_cash_flow(
        current_user.business_id, current_user.id
    )
    return {"summary": res}

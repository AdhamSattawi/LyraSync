import os
import logging
from functools import lru_cache
from typing import AsyncGenerator
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from twilio.request_validator import RequestValidator
from jose import jwt, JWTError
from pydantic import ValidationError
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.infrastructure.database.database import AsyncSessionLocal
from app.infrastructure.ai.audio_transcriber import LLMDataTranscriber
from app.infrastructure.ai.llm_extractor import LLMDataExtractor
from app.infrastructure.database.repositories.conversation_repository import (
    ConversationRepository,
)
from app.infrastructure.adapters.twilio_adapter import TwilioWhatsappAdapter
from app.services.agent_dispatcher import AgentDispatcher
from app.core.config import settings
from app.domain.models.user import User as UserModel
from app.domain.schemas.user_schema import TokenPayload

from app.infrastructure.database.repositories.message_repository import (
    MessageRepository,
)

from app.infrastructure.ai.engines.whisper_engine import OpenAIWhisperEngine
from app.infrastructure.ai.engines.ivrit_engine import IvritEngine
from app.infrastructure.ai.audio_processor import AudioProcessor

# ── Service Layer ────────────────────────────────
from app.services.job_service import JobService
from app.infrastructure.database.repositories.job_repository import JobRepository
from app.infrastructure.database.repositories.client_repository import ClientRepository
from app.infrastructure.database.repositories.business_repository import (
    BusinessRepository,
)
from app.services.transaction_service import TransactionService
from app.infrastructure.database.repositories.transaction_repository import (
    TransactionRepository,
)
from app.services.document_service import DocumentService
from app.services.onboarding_service import OnboardingService
from app.services.subscription_service import SubscriptionService
from app.services.profile_service import ProfileService
from app.infrastructure.database.repositories.job_document_repository import (
    JobDocumentRepository,
)
from app.infrastructure.storage.storage_service import StorageService
from app.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from app.infrastructure.storage.azure_blob_adapter import AzureBlobAdapter

# ── Intent Handlers ───────────────────────────────
from app.services.handlers.draft_quote_handler import DraftQuoteHandler
from app.services.handlers.update_job_handler import UpdateJobHandler
from app.services.handlers.delete_job_handler import DeleteJobHandler
from app.services.handlers.list_jobs_handler import ListJobsHandler
from app.services.handlers.convert_invoice_handler import ConvertInvoiceHandler
from app.services.handlers.log_transaction_handler import LogTransactionHandler
from app.services.handlers.check_balance_handler import CheckBalanceHandler

# ── Model Imports (force SQLAlchemy mapper registration) ──────────────────────
# All models that participate in relationships must be imported before
# the first DB query, or SQLAlchemy raises InvalidRequestError.
from app.domain.models.job_document import JobDocument  # noqa: F401
from app.domain.models.job_item import JobItem  # noqa: F401
from app.domain.models.document_template import DocumentTemplate  # noqa: F401
from app.domain.models.message import Message  # noqa: F401

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger("lyrasync")

limiter = Limiter(key_func=get_remote_address)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login/access-token"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> UserModel:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await db.get(UserModel, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


@lru_cache()
def get_storage_service() -> StorageService:
    """
    Returns the configured StorageService implementation.
    """
    if settings.STORAGE_BACKEND == "azure":
        return AzureBlobAdapter(
            connection_string=settings.AZURE_STORAGE_CONNECTION_STRING,
            container_name=settings.AZURE_STORAGE_CONTAINER_NAME,
            account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
            account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
            sas_expiry_hours=settings.AZURE_SAS_EXPIRY_HOURS,
        )
    return LocalStorageAdapter(base_dir="storage")


@lru_cache()
def get_job_service() -> JobService:
    storage_service = get_storage_service()
    job_doc_repo = JobDocumentRepository()
    document_service = DocumentService(
        session=None,
        job_doc_repo=job_doc_repo,
        storage_service=storage_service,
    )
    return JobService(
        session_maker=AsyncSessionLocal,
        job_repository=JobRepository(),
        client_repository=ClientRepository(),
        business_repository=BusinessRepository(),
        document_service=document_service,
    )


@lru_cache()
def get_transaction_service() -> TransactionService:
    return TransactionService(
        session_maker=AsyncSessionLocal,
        transaction_repository=TransactionRepository(),
        business_repository=BusinessRepository(),
    )


@lru_cache()
def get_onboarding_service() -> OnboardingService:
    return OnboardingService(session_maker=AsyncSessionLocal)


@lru_cache()
def get_profile_service() -> ProfileService:
    return ProfileService(session_maker=AsyncSessionLocal)


@lru_cache()
def get_subscription_service() -> SubscriptionService:
    return SubscriptionService(session_maker=AsyncSessionLocal)


@lru_cache()
def get_agent_dispatcher() -> AgentDispatcher:
    """
    Builds and returns a fully-wired AgentDispatcher singleton.
    """
    job_service = get_job_service()
    transaction_service = get_transaction_service()

    # Assemble handlers
    handlers = [
        DraftQuoteHandler(job_service=job_service),
        UpdateJobHandler(job_service=job_service),
        DeleteJobHandler(job_service=job_service),
        ListJobsHandler(job_service=job_service),
        ConvertInvoiceHandler(job_service=job_service),
        LogTransactionHandler(
            transaction_service=transaction_service, intent_type="log_transaction"
        ),
        CheckBalanceHandler(transaction_service=transaction_service),
    ]

    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    whisper_engine = OpenAIWhisperEngine(client=openai_client)
    ivrit_engine = IvritEngine(api_key=settings.HUGGINGFACE_API_KEY)
    audio_processor = AudioProcessor()
    transcriber = LLMDataTranscriber(
        engines={"whisper": whisper_engine, "ivrit": ivrit_engine},
        processor=audio_processor
    )

    return AgentDispatcher(
        session_maker=AsyncSessionLocal,
        transcriber=transcriber,
        extractor=LLMDataExtractor(client=openai_client),
        conversation_repository=ConversationRepository(),
        handlers=handlers,
        message_repository=MessageRepository(),
    )


def get_twilio_whatsapp_adapter() -> TwilioWhatsappAdapter:
    return TwilioWhatsappAdapter()


async def validate_twilio_request(request: Request):
    """
    Validates that the incoming request came from Twilio.
    """
    if settings.DEBUG:
        return

    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    
    # Get the URL that Twilio called
    url = str(request.url)
    
    # Get the POST parameters
    form_data = await request.form()
    params = dict(form_data)
    
    # Get the signature from the header
    signature = request.headers.get("X-Twilio-Signature")
    
    if not signature or not validator.validate(url, params, signature):
        logger.warning(f"Invalid Twilio signature: {signature} for URL {url}")
        raise HTTPException(status_code=403, detail="Invalid signature")

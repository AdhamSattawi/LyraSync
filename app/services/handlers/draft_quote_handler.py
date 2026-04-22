from app.core.intent_handler import IntentHandler
from app.domain.schemas.intent_schema import IntentType
from app.domain.schemas.job_schema import JobExtract
from app.services.job_service import JobService
import uuid


class DraftQuoteHandler(IntentHandler):
    def __init__(self, job_service: JobService):
        self.job_service = job_service

    @property
    def intent_type(self) -> IntentType:
        return IntentType.DRAFT_QUOTE

    @property
    def extraction_schema(self):
        return JobExtract

    def get_system_prompt(self, profession: str) -> str:
        return (
            f"You are an AI assistant for a {profession} business. "
            "Extract the job details from the user's message to draft a clear quote. "
            "Return the data in the JobExtract schema."
        )

    async def execute(
        self, business_id: uuid.UUID, user_id: uuid.UUID, extracted_data: JobExtract
    ) -> str:
        job = await self.job_service.draft_quote(business_id, user_id, extracted_data)
        total = f"{(job.total_price or 0) / 100:.2f} {job.currency_code}"
        return (
            f"Quote {job.invoice_number} drafted for {job.title}. "
            f"Total: {total}. "
            f"Reply to convert it to an invoice when ready."
        )

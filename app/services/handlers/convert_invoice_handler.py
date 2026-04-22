import uuid
from app.core.intent_handler import IntentHandler
from app.domain.schemas.intent_schema import IntentType
from app.domain.schemas.job_schema import JobIdentifier
from app.domain.schemas.handler_reply import HandlerReply
from app.services.job_service import JobService


class ConvertInvoiceHandler(IntentHandler):
    def __init__(self, job_service: JobService):
        self.job_service = job_service

    @property
    def intent_type(self) -> IntentType:
        return IntentType.CONVERT_TO_INVOICE

    @property
    def extraction_schema(self):
        return JobIdentifier

    def get_system_prompt(self, profession: str) -> str:
        return (
            f"You are an AI assistant for a {profession} business. "
            "Extract the job identifier from the user's message to convert a quote to an invoice. "
            "Return the data in the JobIdentifier schema."
        )

    async def execute(
        self,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        extracted_data: JobIdentifier,
    ) -> str | HandlerReply:
        result = await self.job_service.convert_to_invoice(
            business_id, user_id, extracted_data
        )
        # JobService returns a str for disambiguation/error, or HandlerReply on success.
        # Both are valid — the dispatcher handles each accordingly.
        return result

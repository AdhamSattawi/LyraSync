from app.core.intent_handler import IntentHandler
from app.domain.schemas.intent_schema import IntentType
from app.domain.schemas.job_schema import JobIdentifier
from app.services.job_service import JobService
import uuid


class DeleteJobHandler(IntentHandler):
    def __init__(self, job_service: JobService):
        self.job_service = job_service

    @property
    def intent_type(self) -> IntentType:
        return IntentType.DELETE_JOB

    @property
    def extraction_schema(self):
        return JobIdentifier

    def get_system_prompt(self, profession: str) -> str:
        return (
            f"You are an AI assistant for a {profession} business. "
            "Extract the job identifier from the user's message to delete the job. "
            "Return the data in the JobIdentifier schema."
        )

    async def execute(
        self, business_id: uuid.UUID, user_id: uuid.UUID, extracted_data: JobIdentifier
    ) -> str:
        return await self.job_service.delete_job(business_id, user_id, extracted_data)
